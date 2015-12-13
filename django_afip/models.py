from base64 import b64encode
from datetime import datetime, timedelta, timezone
from subprocess import Popen, PIPE
from tempfile import NamedTemporaryFile
import logging
import random

from django.core.files.base import File
from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext as _
from lxml import etree
from lxml.builder import E

from .utils import format_date, format_datetime, parse_date, parse_datetime, \
    wsaa_client, wsfe_client, AfipException, TZ_AR, encode_str

logger = logging.getLogger(__name__)


def populate_all():
    ReceiptType.objects.populate()
    ConceptType.objects.populate()
    DocumentType.objects.populate()
    VatType.objects.populate()
    TaxType.objects.populate()
    CurrencyType.objects.populate()


class GenericAfipTypeManager(models.Manager):

    def __init__(self, service_name, type_name):
        super().__init__()
        self.__service_name = service_name
        self.__type_name = type_name

    def populate(self, ticket=None):
        """
        Populates the database with valid types retrieved from AFIP's
        webservices.

        If no ticket is provided, the most recent available one will be used.
        """
        ticket = ticket or AuthTicket.objects.get_any_active('wsfe')
        service = getattr(wsfe_client.service, self.__service_name)
        response_xml = service(ticket.ws_object())

        for result in getattr(response_xml.ResultGet, self.__type_name):
            self.get_or_create(
                code=result.Id,
                description=result.Desc.encode("UTF-8"),
                valid_from=parse_date(result.FchDesde),
                valid_to=parse_date(result.FchHasta),
            )


class GenericAfipType(models.Model):
    code = models.CharField(
        _('code'),
        max_length=3,
    )
    description = models.CharField(
        _('description'),
        max_length=250,
    )
    valid_from = models.DateField(
        _('valid from'),
        null=True,
        blank=True,
    )
    valid_to = models.DateField(
        _('valid until'),
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.description

    class Meta:
        abstract = True


class ReceiptType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposCbte', 'CbteTipo')

    class Meta:
        verbose_name = _("receipt type")
        verbose_name_plural = _("receipt types")


class ConceptType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposConcepto', 'ConceptoTipo')

    class Meta:
        verbose_name = _("concept type")
        verbose_name_plural = _("concept types")


class DocumentType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposDoc', 'DocTipo')

    class Meta:
        verbose_name = _("document type")
        verbose_name_plural = _("document types")


class VatType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposIva', 'IvaTipo')

    class Meta:
        verbose_name = _("vat type")
        verbose_name_plural = _("vat types")


class TaxType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposTributos', 'TributoTipo')

    class Meta:
        verbose_name = _("tax type")
        verbose_name_plural = _("tax types")


class CurrencyType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposMonedas', 'Moneda')

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = _("currency type")
        verbose_name_plural = _("currency types")


class TaxPayer(models.Model):
    name = models.CharField(
        _('name'),
        max_length=32,
        help_text=_('A friendly name to recognize this taxpayer.'),
    )
    key = models.FileField(
        _('key'),
        null=True,
    )
    certificate = models.FileField(
        _('certificate'),
        null=True,
    )
    cuit = models.BigIntegerField(
        _('cuit'),
    )

    def create_ticket(self, service):
        ticket = AuthTicket(owner=self, service=service)
        ticket.authorize()
        return ticket

    def get_ticket(self, service):
        return self.auth_tickets \
            .filter(expires__gt=datetime.now(timezone.utc), service=service) \
            .last()

    def get_or_create_ticket(self, service):
        return self.get_ticket(service) or self.create_ticket(service)

    def fetch_points_of_sales(self, ticket=None):
        """
        Fetches all point of sales objects from the WS and stores (or updated)
        them locally.

        Returns a list of tuples with the format (pos, created,).
        """
        ticket = ticket or self.get_or_create_ticket('wsfe')

        response = wsfe_client.service.FEParamGetPtosVenta(
            ticket.ws_object(),
        )
        if hasattr(response, 'Errors'):
            raise AfipException(response.Errors.Err[0])

        results = []
        for pos_data in response.ResultGet.PtoVenta:
            results.append(PointOfSales.objects.update_or_create(
                number=pos_data.Nro,
                issuance_type=pos_data.EmisionTipo,
                owner=self,
                defaults=dict(
                    blocked=pos_data.Bloqueado == 'N',
                    drop_date=parse_date(pos_data.FchBaja),
                )
            ))

        return results

    def __str__(self):
        return str(self.cuit)

    class Meta:
        verbose_name = _("taxpayer")
        verbose_name_plural = _("taxpayers")


class TaxPayerProfile(models.Model):
    """
    Custom information about a taxpayer, used in printed receipts.

    Most of these can be overriden per-invoice, and are usually just defaults.

    None of these are required or sent to the AFIP when notifying about receipt
    generation.
    """
    taxpayer = models.ForeignKey(
        TaxPayer,
        related_name='profile',
        verbose_name=_('taxpayer'),
    )
    issuing_name = models.TextField(
        _('issuing name'),
    )
    issuing_address = models.TextField(
        _('issuing address'),
    )
    issuing_email = models.TextField(
        _('issuing email'),
        blank=True,
        null=True,
    )
    vat_condition = models.CharField(
        max_length=48,
        verbose_name=_('vat condition'),
    )
    gross_income_condition = models.CharField(
        max_length=48,
        verbose_name=_('gross income condition'),
    )
    sales_terms = models.CharField(
        max_length=48,
        verbose_name=_('sales terms'),
        help_text=_(
            'The terms of the sale printed onto receipts by default '
            '(eg: single payment, checking account, etc).'
        ),
    )
    active_since = models.DateField(
        _('active since'),
        help_text=_(
            'Date since which this taxpayer has been legally active.'
        ),
    )

    class Meta:
        verbose_name = _('taxpayer profile')
        verbose_name_plural = _('taxpayer profiles')


class PointOfSales(models.Model):
    number = models.PositiveSmallIntegerField(
        _('number'),
    )
    issuance_type = models.CharField(
        _('issuance type'),
        max_length=8,
        help_text='Indicates if thie POS emits using CAE and CAEA.'
    )
    blocked = models.BooleanField(
        _('blocked'),
    )
    drop_date = models.DateField(
        _('drop date'),
        null=True,
        blank=True,
    )

    owner = models.ForeignKey(
        TaxPayer,
        related_name='points_of_sales',
        verbose_name=_('owner'),
    )

    def __str__(self):
        return str(self.number)

    class Meta:
        unique_together = (
            ('number', 'owner'),
        )
        verbose_name = _('point of sales')
        verbose_name_plural = _('points of sales')


class AuthTicketManager(models.Manager):

    def get_any_active(self, service):
        ticket = AuthTicket.objects.filter(
            token__isnull=False,
            expires__gt=datetime.now(timezone.utc),
            service=service,
        ).first()
        if ticket:
            return ticket

        taxpayer = TaxPayer.objects.order_by('?').first()

        if taxpayer:
            return taxpayer.create_ticket(service)

        raise Exception('There are no taxpayers to generate a ticket.')


class AuthTicket(models.Model):

    def default_generated():
        return datetime.now(TZ_AR)

    def default_expires():
        tomorrow = datetime.now(TZ_AR) + timedelta(hours=12)
        return tomorrow

    def default_unique_id():
        return random.randint(0, 2147483647)

    owner = models.ForeignKey(
        TaxPayer,
        verbose_name=_('owner'),
        related_name='auth_tickets'
    )
    unique_id = models.IntegerField(
        _('unique id'),
        default=default_unique_id,
    )
    generated = models.DateTimeField(
        _('generated'),
        default=default_generated,
    )
    expires = models.DateTimeField(
        _('expires'),
        default=default_expires,
    )
    service = models.CharField(
        _('service'),
        max_length=6,
        help_text=_('Service for which this ticket has been authorized'),
    )

    token = models.TextField(
        _('token'),
    )
    signature = models.TextField(
        _('signature'),
    )

    objects = AuthTicketManager()

    TOKEN_XPATH = "/loginTicketResponse/credentials/token"
    SIGN_XPATH = "/loginTicketResponse/credentials/sign"

    def __create_request_xml(self):
        request_xml = (
            E.loginTicketRequest(
                {'version': '1.0'},
                E.header(
                    E.uniqueId(str(self.unique_id)),
                    E.generationTime(format_datetime(self.generated)),
                    E.expirationTime(format_datetime(self.expires)),
                ),
                E.service(self.service)
            )
        )
        return etree.tostring(request_xml, pretty_print=True)

    def __sign_request(self, request):
        cert = self.owner.certificate.file.name
        key = self.owner.key.file.name

        return Popen(
            [
                "openssl", "smime", "-sign", "-signer", cert, "-inkey", key,
                "-outform", "DER", "-nodetach"
            ],
            stdin=PIPE, stdout=PIPE, stderr=PIPE
        ).communicate(request)[0]

    def authorize(self, save=True):
        request = self.__create_request_xml()
        request = self.__sign_request(request)
        request = b64encode(request).decode()

        raw_response = wsaa_client.service.loginCms(request)
        response = etree.fromstring(raw_response.encode('utf-8'))

        self.token = response.xpath(self.TOKEN_XPATH)[0].text
        self.signature = response.xpath(self.SIGN_XPATH)[0].text
        if save:
            self.save()

    def ws_object(self):
        """
        Returns this object as an object compatible with AFIP's web services.
        """
        wso = wsfe_client.factory.create('FEAuthRequest')
        wso.Token = self.token
        wso.Sign = self.signature
        wso.Cuit = self.owner.cuit

        return wso

    def __str__(self):
        return str(self.unique_id)

    class Meta:
        verbose_name = _('authorization ticket')
        verbose_name_plural = _('authorization tickets')


class ReceiptBatchManager(models.Manager):

    def create(self, queryset):
        """
        Creates a batch with all receipts returned by ``queryset``.
        """
        first = queryset.select_related('point_of_sales').first()
        if not first:
            # Queryset is empty, nothing to create
            return
        batch = ReceiptBatch(
            receipt_type_id=first.receipt_type_id,
            point_of_sales_id=first.point_of_sales_id,
        )
        batch.save()

        # Exclude any receipts that are already batched (either pre-selection,
        # or due to concurrency):
        queryset.filter(batch__isnull=True).update(batch=batch)
        return batch


class ReceiptBatch(models.Model):
    """
    Receipts are validated sent in batches.
    """

    receipt_type = models.ForeignKey(
        ReceiptType,
        verbose_name=_('receipt type'),
    )
    point_of_sales = models.ForeignKey(
        PointOfSales,
        verbose_name=_('point of sales'),
    )

    def __str__(self):
        return str(self.id)

    def ws_object(self):
        """
        Returns this object as an object compatible with AFIP's web services.
        """
        receipts = self.receipts.all().order_by('receipt_number')

        wso = wsfe_client.factory.create('FECAERequest')
        wso.FeCabReq.CantReg = len(receipts)
        wso.FeCabReq.PtoVta = self.point_of_sales.number
        wso.FeCabReq.CbteTipo = self.receipt_type.code

        for receipt in receipts:
            wso.FeDetReq.FECAEDetRequest.append(receipt.ws_object())

        return wso

    def validate(self, ticket=None):
        if self.receipts.count() == 0:
            logger.debug("Refusing to validate empty Batch")
            return
        if self.receipts.filter(validation__isnull=True).count() == 0:
            logger.debug("Refusing to Batch with no non-validated Receipts")
            return

        ticket = ticket or \
            self.point_of_sales.owner.get_or_create_ticket('wsfe')

        next_num = Receipt.objects.fetch_last_receipt_number(
            self.point_of_sales,
            self.receipt_type,
        ) + 1
        for receipt in self.receipts.filter(receipt_number__isnull=True):

            # Atomically update receipt number
            Receipt.objects \
                .filter(pk=receipt.id, receipt_number__isnull=True) \
                .update(receipt_number=next_num)
            next_num += 1

        # Purge the internal cache (.update() doesn't maintan it)
        self.receipts.all()

        response = wsfe_client.service.FECAESolicitar(
            ticket.ws_object(),
            self.ws_object(),
        )

        if hasattr(response, 'Errors'):
            raise AfipException(response.Errors.Err[0])

        validation = Validation.objects.create(
            processed_date=parse_datetime(response.FeCabResp.FchProceso),
            result=response.FeCabResp.Resultado,
            batch=self,
        )

        errs = []
        for cae_data in response.FeDetResp.FECAEDetResponse:
            if cae_data.Resultado == Validation.RESULT_APPROVED:
                rv = validation.receipts.create(
                    result=cae_data.Resultado,
                    cae=cae_data.CAE,
                    cae_expiration=parse_date(cae_data.CAEFchVto),
                    receipt=self.receipts.get(
                        receipt_number=cae_data.CbteDesde
                    ),
                )
                if hasattr(cae_data, 'Observaciones'):
                    for obs in cae_data.Observaciones.Obs:
                        observation = Observation.objects.get_or_create(
                            code=obs.Code,
                            message=obs.Msg,
                        )
                    rv.observations.add(observation)
            elif hasattr(cae_data, 'Observaciones'):
                for obs in cae_data.Observaciones.Obs:
                    errs.append(
                        "Error {}: {}".format(
                            obs.Code,
                            encode_str(obs.Msg),
                        )
                    )

        # Remove failed receipts from the batch
        self.receipts.filter(validation__isnull=True) \
            .update(batch=None, receipt_number=None)

        return errs

    class Meta:
        verbose_name = _('receipt batch')
        verbose_name_plural = _('receipt batches')

    objects = ReceiptBatchManager()


class ReceiptManager(models.Manager):

    def fetch_last_receipt_number(self, point_of_sales, receipt_type):
        response_xml = wsfe_client.service.FECompUltimoAutorizado(
            point_of_sales.owner.get_or_create_ticket('wsfe').ws_object(),
            point_of_sales.number,
            receipt_type.code,
        )

        # TODO XXX: Error handling
        # (FERecuperaLastCbteResponse){
        #    PtoVta = 0
        #    CbteTipo = 0
        #    CbteNro = 0
        #    Errors =
        #       (ArrayOfErr){
        #          Err[] =
        #             (Err){
        #                Code = 601
        #                Msg = "CUIT representada no incluida en Token"
        #             },
        #       }
        #  }

        return response_xml.CbteNro

    def get_queryset(self):
        return super().get_queryset().select_related(
            'receipt_type',
        )


class Receipt(models.Model):
    """
    A receipt, as sent to AFIP.

    Note that AFIP allows sending ranges of receipts, but this isn't generally
    what you want, so we model invoices individually.

    You'll probably want to relate some `Sale` or `Order` object from your
    model with each Receipt.
    """
    batch = models.ForeignKey(
        ReceiptBatch,
        related_name='receipts',
        null=True,
        blank=True,
        verbose_name=_('receipt batch'),
        help_text=_(
            'Receipts are validated in batches, so it must be assigned one '
            'before validation is possible.'
        ),
        on_delete=models.PROTECT,
    )
    concept = models.ForeignKey(
        ConceptType,
        verbose_name=_('concept'),
        related_name='receipts',
    )
    document_type = models.ForeignKey(
        DocumentType,
        verbose_name=_('document type'),
        related_name='receipts',
        help_text=_(
            'The document type of the customer to whom this receipt '
            'is addressed'
        ),
    )
    document_number = models.BigIntegerField(
        _('document number'),
        help_text=_(
            'The document number of the customer to whom this receipt '
            'is addressed'
        )
    )
    # NOTE: WS will expect receipt_from and receipt_to.
    receipt_number = models.PositiveIntegerField(
        _('receipt number'),
        null=True,
        blank=True,
    )
    issued_date = models.DateField(
        verbose_name=_('issued date'),
        help_text=_('Can diverge up to 5 days for good, or 10 days otherwise'),
    )
    total_amount = models.DecimalField(
        # ImpTotal
        _('total amount'),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            'Must be equal to untaxed amount + exempt amount + taxes + vat.'
        )
    )
    net_untaxed = models.DecimalField(
        # ImpTotConc
        _('total untaxable amount'),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            'The total amount to which taxes do not apply. '
            'For C-type receipts, this must be zero.'
        ),
    )
    net_taxed = models.DecimalField(
        # ImpNeto
        _('total taxable amount'),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            'The total amount to which taxes apply. '
            'For C-type receipts, this is equal to the subtotal.'
            ),
    )
    exempt_amount = models.DecimalField(
        # ImpOpEx
        # Sólo para emisores que son IVA exento
        _('exempt amount'),
        max_digits=15,
        decimal_places=2,
        help_text=_(
            'Only for categories which are tax-exempt. '
            'For C-type receipts, this must be zero.'
        ),
    )
    # Runtime-calculated. Deleteable?
    # vat_amount = models.DecimalField(
    #     _('vat amount'),
    #     max_digits=15,
    #     decimal_places=2,
    #     help_text=_('Must be equal to the sum of all Vat objects.'),
    # )
    # tax_amount = models.DecimalField(
    #     _('tax amount'),
    #     max_digits=15,
    #     decimal_places=2,
    #     help_text=_('Must be equal to the sum of all Tax objects.'),
    # )
    service_start = models.DateField(
        _('service start date'),
        help_text=_(
            'Date on which a service started. No applicable for goods.'
        ),
        null=True,
        blank=True,
    )
    service_end = models.DateField(
        _('service end date'),
        help_text=_(
            'Date on which a service ended. No applicable for goods.'
        ),
        null=True,
        blank=True,
    )
    expiration_date = models.DateField(
        _('receipt expiration date'),
        help_text=_(
            'Date on which this receipt expires. No applicable for goods.'
        ),
        null=True,
        blank=True,
    )
    currency = models.ForeignKey(
        CurrencyType,
        verbose_name=_('currency'),
        related_name='documents',
        help_text=_(
            'Currency in which this receipt is issued.',
        ),
    )
    currency_quote = models.DecimalField(
        _('currency quote'),
        max_digits=10,
        decimal_places=6,
        help_text=_(
            'Quote of the day for the currency used in the receipt',
        ),
        # XXX: Is this always mandatory?
    )
    related_receipts = models.ManyToManyField(
        'Receipt',
        verbose_name=_('related receipts'),
        blank=True,
    )

    objects = ReceiptManager()

    def auto_set_receipt_number(self, ticket=None):
        """
        Automatically sets this receipts number.
        It is recomended that you let ``validate`` do this, rather than handle
        it manually.
        """
        ticket = ticket or \
            self.point_of_sales.owner.get_or_create_ticket('wsfe')

        next_num = Receipt.objects.fetch_last_receipt_number(
            self.point_of_sales,
            self.receipt_type,
        ) + 1

        # Atomically update receipt number
        # XXX: ¿Use select for update?
        Receipt.objects.filter(pk=self.id, receipt_number__isnull=True) \
            .update(receipt_number=next_num)
        self.receipt_number = next_num
        # TODO: handle error.

    def ws_object(self):
        """
        Returns this object as an object compatible with AFIP's web services.
        """

        subtotals = Receipt.objects.filter(pk=self.pk).aggregate(
            vat=Sum('vat__amount', distinct=True),
            taxes=Sum('taxes__amount', distinct=True),
        )

        wso = wsfe_client.factory.create('FECAEDetRequest')
        wso.Concepto = self.concept.code
        wso.DocTipo = self.document_type.code
        wso.DocNro = self.document_number
        # TODO: Check that this is not None!
        wso.CbteDesde = self.receipt_number
        wso.CbteHasta = self.receipt_number
        wso.CbteFch = format_date(self.issued_date)
        wso.ImpTotal = self.total_amount
        wso.ImpTotConc = self.net_untaxed
        wso.ImpNeto = self.net_taxed
        wso.ImpOpEx = self.exempt_amount
        wso.ImpIVA = subtotals['vat'] or 0
        wso.ImpTrib = subtotals['taxes'] or 0
        if int(self.concept.code) in (2, 3,):
            wso.FchServDesde = format_date(self.service_start)
            wso.FchServHasta = format_date(self.service_end)
            wso.FchVtoPago = format_date(self.expiration_date)
        wso.MonId = self.currency.code
        wso.MonCotiz = self.currency_quote

        for tax in self.taxes.all():
            wso.Tributos.Tributo.append(tax.ws_object())

        for vat in self.vat.all():
            wso.Iva.AlicIva.append(vat.ws_object())

        # XXX: Need to create a CbteAsoc object:
        for receipt in self.related_receipts.all():
            receipt_wso = wsfe_client.factory.create('CbteAsoc')
            receipt_wso.receipt.receipt_type.code
            receipt_wso.receipt.point_of_sales.number
            receipt_wso.receipt.receipt_number
            wso.CbtesAsoc.append(receipt_wso)

        return wso

    # Not implemented: optionals

    # TODO: methods to validate total

    # These two values are stored in the receipt's batch. However, before the
    # receipt is assigned into a batch, this value should be used.
    receipt_type = models.ForeignKey(
        ReceiptType,
        related_name='receipts',
        verbose_name=_('receipt type'),
    )
    point_of_sales = models.ForeignKey(
        PointOfSales,
        related_name='receipts',
        verbose_name=_('point of sales'),
    )

    def __str__(self):
        if self.receipt_number:
            return '<{}> {} #{}'.format(
                self.pk,
                self.receipt_type,
                self.receipt_number,
            )
        else:
            return _('<%(id)s> %(receipt_type)s') \
                % {'receipt_type': self.receipt_type, 'id': self.pk}

    class Meta:
        verbose_name = _('receipt')
        verbose_name_plural = _('receipts')
        unique_together = (
            ('point_of_sales', 'receipt_type', 'receipt_number',)
        )
        # TODO: index_together...


class ReceiptPDFManager(models.Manager):

    def create_for_receipt(self, receipt, profile=None):
        """
        Creates a ReceiptPDF object for a given receipt. Does not actually
        generate the related PDF file.
        """
        profile = profile or TaxPayerProfile.objects.get(
            taxpayer__points_of_sales__receipts=receipt,
        )
        pdf = ReceiptPDF.objects.create(
            receipt=receipt,
            issuing_name=profile.issuing_name,
            issuing_address=profile.issuing_address,
            issuing_email=profile.issuing_email,
            vat_condition=profile.vat_condition,
            gross_income_condition=profile.gross_income_condition,
            sales_terms=profile.sales_terms,
        )
        return pdf


class ReceiptPDF(models.Model):
    receipt = models.OneToOneField(
        Receipt,
        verbose_name=_('receipt'),
    )
    pdf_file = models.FileField(
        verbose_name=_('pdf file'),
        blank=True,
        null=True,
    )
    issuing_name = models.CharField(
        max_length=128,
        verbose_name=_('issuing name'),
    )
    issuing_address = models.TextField(
        _('issuing address'),
    )
    issuing_email = models.CharField(
        max_length=128,
        verbose_name=_('issuing email'),
        null=True,
    )
    vat_condition = models.CharField(
        max_length=48,
        verbose_name=_('vat condition'),
        # IVA Responsable Inscripto
        # No responsable IVA
        # IVA Exento
        # A consumidor Final
    )
    gross_income_condition = models.CharField(
        max_length=48,
        verbose_name=_('gross income condition'),
    )
    client_name = models.CharField(
        max_length=128,
        verbose_name=_('client name'),
    )
    client_address = models.TextField(
        _('client address'),
    )
    sales_terms = models.CharField(
        max_length=48,
        verbose_name=_('sales terms'),
        # Contado, Cta corriente, etc...
    )

    objects = ReceiptPDFManager()

    def save_pdf(self):
        """
        Saves the receipt as a PDF related to this model.
        """
        from . import pdf
        with NamedTemporaryFile(suffix='.pdf') as file_:
            pdf.generate_receipt_pdf(self.receipt_id, file_)
            self.pdf_file = File(file_)
            self.save()

    def save_pdf_to(self, file_):
        """
        Saves the receipt as an actual PDF file into a custom location.
        """
        from . import pdf
        pdf.generate_receipt_pdf(self.receipt_id, file_)

    class Meta:
        verbose_name = _('receipt pdf')
        verbose_name_plural = _('receipt pdfs')


class ReceiptEntry(models.Model):
    receipt = models.ForeignKey(
        Receipt,
        related_name='entries',
        verbose_name=_('receipt'),
    )
    description = models.CharField(
        max_length=128,
        verbose_name=_('description'),
    )
    amount = models.PositiveSmallIntegerField(
        _('amount'),
    )
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=15,
        decimal_places=2,
    )

    @property
    def total_price(self):
        return self.amount * self.unit_price

    class Meta:
        verbose_name = _('receipt entry')
        verbose_name_plural = _('receipt entries')


class Tax(models.Model):
    tax_type = models.ForeignKey(
        TaxType,
        verbose_name=_('tax type'),
    )
    description = models.CharField(
        _('description'),
        max_length=80,
    )
    base_amount = models.DecimalField(
        _('base amount'),
        max_digits=15,
        decimal_places=2,
    )
    aliquot = models.DecimalField(
        _('aliquot'),
        max_digits=5,
        decimal_places=2,
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=15,
        decimal_places=2,
    )

    receipt = models.ForeignKey(
        Receipt,
        related_name='taxes',
    )

    def compute_amount(self):
        self.amount = self.base_amount * self.aliquot / 100
        return self.amount

    def ws_object(self):
        """
        Returns this object as an object compatible with AFIP's web services.
        """
        wso = wsfe_client.factory.create('Tributo')
        wso.Id = self.tax_type.code
        wso.Desc = self.description
        wso.BaseImp = self.base_amount
        wso.Alic = self.aliquot
        wso.Importe = self.amount

        return wso

    class Meta:
        verbose_name = _('tax')
        verbose_name_plural = _('taxes')


class Vat(models.Model):
    vat_type = models.ForeignKey(
        VatType,
        verbose_name=_('vat type'),
    )
    base_amount = models.DecimalField(
        _('base amount'),
        max_digits=15,
        decimal_places=2,
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=15,
        decimal_places=2,
    )

    receipt = models.ForeignKey(
        Receipt,
        related_name='vat',
    )

    def ws_object(self):
        """
        Returns this object as an object compatible with AFIP's web services.
        """
        wso = wsfe_client.factory.create('AlicIva')
        wso.Id = self.vat_type.code
        wso.BaseImp = self.base_amount
        wso.Importe = self.amount

        return wso

    class Meta:
        verbose_name = _('vat')
        verbose_name_plural = _('vat')


class Validation(models.Model):
    RESULT_APPROVED = 'A'
    RESULT_REJECTED = 'R'
    RESULT_PARTIAL = 'P'

    processed_date = models.DateTimeField(
        _('processed date'),
    )
    result = models.CharField(
        _('result'),
        max_length=1,
        choices=(
            (RESULT_APPROVED, _('approved')),
            (RESULT_REJECTED, _('rejected')),
            (RESULT_PARTIAL, _('partial')),
        ),
    )

    # reprocessed?

    batch = models.ForeignKey(
        ReceiptBatch,
        related_name='validation',
        verbose_name=_('receipt batch'),
    )

    class Meta:
        verbose_name = _('validation')
        verbose_name_plural = _('validations')


class Observation(models.Model):
    code = models.PositiveSmallIntegerField(
        _('code'),
    )
    message = models.CharField(
        _('message'),
        max_length=255,
    )

    class Meta:
        verbose_name = _('observation')
        verbose_name_plural = _('observations')


class ReceiptValidation(models.Model):
    validation = models.ForeignKey(
        Validation,
        verbose_name=_('validation'),
        related_name='receipts',
    )
    result = models.CharField(
        _('result'),
        max_length=1,
        choices=(
            (Validation.RESULT_APPROVED, _('approved')),
            (Validation.RESULT_REJECTED, _('rejected')),
            (Validation.RESULT_PARTIAL, _('partial')),
        ),
    )
    cae = models.CharField(
        _('cae'),
        max_length=14
    )
    cae_expiration = models.DateField(
        _('cae expiration'),
    )
    observations = models.ManyToManyField(
        Observation,
        verbose_name=_('observations'),
        related_name='valiations',
    )

    receipt = models.OneToOneField(
        Receipt,
        related_name='validation',
        verbose_name=_('receipt'),
    )

    class Meta:
        verbose_name = _('receipt validation')
        verbose_name_plural = _('receipt validations')
