import io
import logging
import random
import uuid
from base64 import b64encode
from datetime import datetime, timedelta, timezone
from tempfile import NamedTemporaryFile

import pytz
from django.core.files.base import File
from django.db import models
from django.utils.translation import ugettext_lazy as _
from lxml import etree
from lxml.builder import E
from zeep.exceptions import Fault

from . import clients, crypto, exceptions, parsers, serializers

logger = logging.getLogger(__name__)
TZ_AR = pytz.timezone(pytz.country_timezones['ar'][0])


def populate_all():
    """Fetch and store all metadata from the AFIP."""
    ReceiptType.objects.populate()
    ConceptType.objects.populate()
    DocumentType.objects.populate()
    VatType.objects.populate()
    TaxType.objects.populate()
    CurrencyType.objects.populate()


def check_response(response):
    """
    Check that a response is not an error.

    AFIP allows us to create valid tickets with invalid key/CUIT pairs, so we
    can end up with tickets that fail on any service.

    Due to how zeep works, we can't quite catch these sort of errors on some
    middleware level (well, honestly, we need to do a large refactor).

    This method checks if responses have an error, and raise a readable
    message.
    """
    if response.Errors:
        raise exceptions.AfipException(response)


class GenericAfipTypeManager(models.Manager):
    """Default Manager for GenericAfipType."""

    def __init__(self, service_name, type_name):
        """
        Create a new Manager instance for a GenericAfipType.

        This should generally only be required to manually populate a single
        type with upstream data.
        """
        super().__init__()
        self.__service_name = service_name
        self.__type_name = type_name

    def populate(self, ticket=None):
        """
        Populate the database with types retrieved from the AFIP.

        If no ticket is provided, the most recent available one will be used.
        """
        ticket = ticket or AuthTicket.objects.get_any_active('wsfe')
        client = clients.get_client('wsfe', ticket.owner.is_sandboxed)
        service = getattr(client.service, self.__service_name)
        response_xml = service(serializers.serialize_ticket(ticket))

        check_response(response_xml)

        for result in getattr(response_xml.ResultGet, self.__type_name):
            self.get_or_create(
                code=result.Id,
                description=result.Desc.encode('UTF-8'),
                valid_from=parsers.parse_date(result.FchDesde),
                valid_to=parsers.parse_date(result.FchHasta),
            )


class GenericAfipType(models.Model):
    """An abstract class for several of AFIP's metadata types."""

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
    """
    An AFIP receipt type.

    See the AFIP's documentation for details on each receipt type.
    """

    objects = GenericAfipTypeManager('FEParamGetTiposCbte', 'CbteTipo')

    class Meta:
        verbose_name = _('receipt type')
        verbose_name_plural = _('receipt types')


class ConceptType(GenericAfipType):
    """
    An AFIP concept type.

    See the AFIP's documentation for details on each concept type.
    """

    objects = GenericAfipTypeManager('FEParamGetTiposConcepto', 'ConceptoTipo')

    class Meta:
        verbose_name = _('concept type')
        verbose_name_plural = _('concept types')


class DocumentType(GenericAfipType):
    """
    An AFIP document type.

    See the AFIP's documentation for details on each document type.
    """

    objects = GenericAfipTypeManager('FEParamGetTiposDoc', 'DocTipo')

    class Meta:
        verbose_name = _('document type')
        verbose_name_plural = _('document types')


class VatType(GenericAfipType):
    """
    An AFIP VAT type.

    See the AFIP's documentation for details on each VAT type.
    """

    objects = GenericAfipTypeManager('FEParamGetTiposIva', 'IvaTipo')

    class Meta:
        verbose_name = _('vat type')
        verbose_name_plural = _('vat types')


class TaxType(GenericAfipType):
    """
    An AFIP tax type.

    See the AFIP's documentation for details on each tax type.
    """

    objects = GenericAfipTypeManager('FEParamGetTiposTributos', 'TributoTipo')

    class Meta:
        verbose_name = _('tax type')
        verbose_name_plural = _('tax types')


class CurrencyType(GenericAfipType):
    """
    An AFIP curreny type.

    See the AFIP's documentation for details on each currency type.
    """

    objects = GenericAfipTypeManager('FEParamGetTiposMonedas', 'Moneda')

    def __str__(self):
        return self.code

    class Meta:
        verbose_name = _('currency type')
        verbose_name_plural = _('currency types')


class TaxPayer(models.Model):
    """
    Represents an AFIP TaxPayer.

    This class has the bare minimum required for most AFIP services.

    Note that multiple instances of this object can actually represent the same
    taxpayer, each using a different key.
    """

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
    is_sandboxed = models.BooleanField(
        _('is sandboxed'),
        help_text=_(
            'Indicates if this taxpayer interacts with the sandbox servers '
            'rather than the production servers'
        )
    )

    def generate_key(self, force=False):
        """
        Creates a key file for this TaxPayer

        Creates a key file for this TaxPayer if it does not have one, and
        immediately saves it.

        Returns True if and only if a key was created.
        """
        if self.key and not force:
            logger.warning(
                'Tried to generate key for a taxpayer that already had one'
            )
            return False

        with NamedTemporaryFile(suffix='.key') as file_:
            crypto.create_key(file_)
            self.key = File(file_, name='{}.key'.format(uuid.uuid4().hex))
            self.save()

        return True

    def generate_csr(self, basename='djangoafip'):
        """
        Creates a CSR for this TaxPayer's key

        Creates a file-like object that contains the CSR which can be used to
        request a new certificate from AFIP.
        """
        csr = io.BytesIO()
        crypto.create_csr(
            self.key.file,
            self.name,
            '{}{}'.format(basename, int(datetime.now().timestamp())),
            'CUIT {}'.format(self.cuit),
            csr,
        )
        csr.seek(0)
        return csr

    def create_ticket(self, service):
        """Create an AuthTicket for a given service."""
        ticket = AuthTicket(owner=self, service=service)
        ticket.authorize()
        return ticket

    def get_ticket(self, service):
        """Return an existing AuthTicket for a given service."""
        return self.auth_tickets \
            .filter(expires__gt=datetime.now(timezone.utc), service=service) \
            .last()

    def get_or_create_ticket(self, service):
        """
        Return or create a new AuthTicket for a given serivce.

        Return an existing ticket for a service if one is available, otherwise,
        create a new one and return that.

        This is generally the preferred method of obtaining tickets for any
        service.
        """
        return self.get_ticket(service) or self.create_ticket(service)

    def fetch_points_of_sales(self, ticket=None):
        """
        Fetch all point of sales objects.

        Fetch all point of sales from the WS and store (or update) them
        locally.

        Returns a list of tuples with the format (pos, created,).
        """
        ticket = ticket or self.get_or_create_ticket('wsfe')

        client = clients.get_client('wsfe', self.is_sandboxed)
        response = client.service.FEParamGetPtosVenta(
            serializers.serialize_ticket(ticket),
        )
        check_response(response)

        results = []
        for pos_data in response.ResultGet.PtoVenta:
            results.append(PointOfSales.objects.update_or_create(
                number=pos_data.Nro,
                issuance_type=pos_data.EmisionTipo,
                owner=self,
                defaults=dict(
                    blocked=pos_data.Bloqueado == 'N',
                    drop_date=parsers.parse_date(pos_data.FchBaja),
                )
            ))

        return results

    def __str__(self):
        return str(self.cuit)

    class Meta:
        verbose_name = _('taxpayer')
        verbose_name_plural = _('taxpayers')


class TaxPayerProfile(models.Model):
    """
    Custom information about a taxpayer, used in printed receipts.

    Most of these can be overriden per-receipt, and are usually just defaults.

    None of these are required or sent to the AFIP when notifying about receipt
    generation. They are used *only* for PDF generation.
    """

    taxpayer = models.OneToOneField(
        TaxPayer,
        related_name='profile',
        verbose_name=_('taxpayer'),
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
    """
    Represents an existing AFIP point of sale.

    Points of sales need to be created via AFIP's web interface and it is
    recommended that you use :meth:`~.TaxPayer.fetch_points_of_sales` to fetch
    these programatically.
    """
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

        if not taxpayer:
            raise exceptions.AuthenticationError(
                _('There are no taxpayers to generate a ticket.'),
            )

        return taxpayer.create_ticket(service)


class AuthTicket(models.Model):
    """
    An AFIP Authorization ticket.

    This is a signed ticket used to communicate with AFIP's webservices.

    Applications should not generally have to deal with these tickets
    themselves; most services will find or create one as necessary.
    """

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

    TOKEN_XPATH = '/loginTicketResponse/credentials/token'
    SIGN_XPATH = '/loginTicketResponse/credentials/sign'

    def __create_request_xml(self):
        request_xml = (
            E.loginTicketRequest(
                {'version': '1.0'},
                E.header(
                    E.uniqueId(str(self.unique_id)),
                    E.generationTime(
                        serializers.serialize_datetime(self.generated)
                    ),
                    E.expirationTime(
                        serializers.serialize_datetime(self.expires)
                    ),
                ),
                E.service(self.service)
            )
        )
        return etree.tostring(request_xml, pretty_print=True)

    def __sign_request(self, request):
        with open(self.owner.certificate.file.name) as cert_file:
            cert = cert_file.read()

        with open(self.owner.key.file.name) as key_file:
            key = key_file.read()

        return crypto.create_embeded_pkcs7_signature(request, cert, key)

    def authorize(self):
        """Send this ticket to AFIP for authorization."""
        request = self.__create_request_xml()
        request = self.__sign_request(request)
        request = b64encode(request).decode()

        client = clients.get_client('wsaa', self.owner.is_sandboxed)
        try:
            raw_response = client.service.loginCms(request)
        except Fault as e:
            if e.message == 'Certificado expirado':
                raise exceptions.CertificateExpired(e.message) from e
            if e.message == 'Certificado no emitido por AC de confianza':
                raise exceptions.UntrustedCertificate(e.message) from e
            raise exceptions.AuthenticationError(e.message) from e
        response = etree.fromstring(raw_response.encode('utf-8'))

        self.token = response.xpath(self.TOKEN_XPATH)[0].text
        self.signature = response.xpath(self.SIGN_XPATH)[0].text

        self.save()

    def __str__(self):
        return str(self.unique_id)

    class Meta:
        verbose_name = _('authorization ticket')
        verbose_name_plural = _('authorization tickets')


class ReceiptBatchManager(models.Manager):

    def create(self, queryset):
        """
        Creates a batch with all receipts returned by ``queryset``.

        If you need to create a ReceiptBatch with a single receipt, just
        pass a query that returns that one::

            Receipt.objects.filter(pk=pk)
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
    Receipts are validated in batches.

    AFIP's webservice validates receipts in batches, and this class models
    them. A batch of receipts is simply a set of consecutive-numbered
    :class:`~.Receipt` instances, with the same :class:`~.ReceiptType` and
    :class:`~.PointOfSales`.

    If you need to validate a single Receipt, it's okay to create a batch with
    just one.
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

    def validate(self, ticket=None):
        """
        Validates all receipts assigned to this batch.

        Attempting to validate an empty batch will do nothing.

        Any receipts that fail validation are removed from the batch, so you
        should never modify a batch after validation. Receipts that succesfully
        validae will have a :class:`~.ReceiptValidation` object attatched to
        them with a validation date and CAE information.

        Returns a list of errors as returned from AFIP's webservices. An
        exception is not raised because partial failures are possible.
        """
        if self.receipts.count() == 0:
            logger.debug('Refusing to validate empty Batch')
            return []
        if self.receipts.filter(validation__isnull=True).count() == 0:
            logger.debug('Refusing to Batch with no non-validated Receipts')
            return []

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

        client = clients.get_client(
            'wsfe', self.point_of_sales.owner.is_sandboxed
        )
        response = client.service.FECAESolicitar(
            serializers.serialize_ticket(ticket),
            serializers.serialize_receipt_batch(self),
        )
        check_response(response)

        if response.Errors:
            raise exceptions.AfipException(response)

        validation = Validation.objects.create(
            processed_date=parsers.parse_datetime(
                response.FeCabResp.FchProceso
            ),
            result=response.FeCabResp.Resultado,
            batch=self,
        )

        errs = []
        for cae_data in response.FeDetResp.FECAEDetResponse:
            if cae_data.Resultado == Validation.RESULT_APPROVED:
                rv = validation.receipts.create(
                    result=cae_data.Resultado,
                    cae=cae_data.CAE,
                    cae_expiration=parsers.parse_date(cae_data.CAEFchVto),
                    receipt=self.receipts.get(
                        receipt_number=cae_data.CbteDesde
                    ),
                )
                if cae_data.Observaciones:
                    for obs in cae_data.Observaciones.Obs:
                        observation = Observation.objects.get_or_create(
                            code=obs.Code,
                            message=obs.Msg,
                        )
                    rv.observations.add(observation)
            elif cae_data.Observaciones:
                for obs in cae_data.Observaciones.Obs:
                    errs.append(
                        'Error {}: {}'.format(
                            obs.Code,
                            parsers.parse_string(obs.Msg),
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


class ReceiptQuerySet(models.QuerySet):
    """
    The default queryset obtains when querying via :class:`~.ReceiptManager`.
    """

    def validate(self, ticket=None):
        """
        Validates all receipts matching this queryset.

        Note that, due to how AFIP implements its numbering, this method is not
        thread-safe, or even multiprocess-safe.

        Because of this, it is possible that not all instances matching this
        queryset are validates properly; however, consistency *is* and receipts
        will be updated if and only if they have been validated by the AFIP.
        """
        return ReceiptBatch.objects.create(self).validate(ticket)


class ReceiptManager(models.Manager):
    """
    The default manager for the :class:`~.Receipt` class.

    You should generally access this using ``Receipt.objects``.
    """

    def fetch_last_receipt_number(self, point_of_sales, receipt_type):
        client = clients.get_client('wsfe', point_of_sales.owner.is_sandboxed)
        response_xml = client.service.FECompUltimoAutorizado(
            serializers.serialize_ticket(
                point_of_sales.owner.get_or_create_ticket('wsfe')
            ),
            point_of_sales.number,
            receipt_type.code,
        )
        check_response(response_xml)

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
        return ReceiptQuerySet(self.model, using=self._db).select_related(
            'receipt_type',
        )


class Receipt(models.Model):
    """
    A receipt, as sent to AFIP.

    Note that AFIP allows sending ranges of receipts, but this isn't generally
    what you want, so we model invoices individually.

    To validate a Receipt, you need to create a :class:`~.ReceiptBatch` first.

    You'll probably want to relate some `Sale` or `Order` object from your
    model with each Receipt.

    All ``document_`` fields contain the recipient's data.

    If the taxpayer has taxes or pays VAT, you need to attach :class:`~.Tax`
    and/or :class:`~.Vat` instances to the Receipt.
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

    # TODO: Not implemented: optionals
    # TODO: methods to validate totals

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

    def validate(self, ticket=None):
        """
        Validates this receipt.

        This is a shortcut to :class:`~.ReceiptQuerySet`'s method of the same
        name. Calling this validates only this instance.
        """
        rv = Receipt.objects.filter(pk=self.pk).validate(ticket)
        # Since we're operating via a queryset, this instance isn't properly
        # updated:
        self.refresh_from_db()
        return rv

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

    def create_for_receipt(self, receipt, **kwargs):
        """
        Creates a ReceiptPDF object for a given receipt. Does not actually
        generate the related PDF file.

        :param Receipt receipt: The receipt for the PDF will be generated.
        """
        try:
            profile = TaxPayerProfile.objects.get(
                taxpayer__points_of_sales__receipts=receipt,
            )
        except TaxPayerProfile.DoesNotExist:
            raise Exception(
                'Cannot generate a PDF for taxpayer with no profile',
            )
        pdf = ReceiptPDF.objects.create(
            receipt=receipt,
            issuing_name=profile.issuing_name,
            issuing_address=profile.issuing_address,
            issuing_email=profile.issuing_email,
            vat_condition=profile.vat_condition,
            gross_income_condition=profile.gross_income_condition,
            sales_terms=profile.sales_terms,
            **kwargs
        )
        return pdf


class ReceiptPDF(models.Model):
    """
    Printable version of a receipt.

    Models all print-related data of a receipt and references generated PDF
    files.

    All `issuing`` fields contain data for the entity issuing the Receipt
    (these may change from one receipt to the next if, for example, the entity
    moved).
    """
    receipt = models.OneToOneField(
        Receipt,
        verbose_name=_('receipt'),
    )
    pdf_file = models.FileField(
        verbose_name=_('pdf file'),
        upload_to='receipts',
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
        blank=True,
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
        help_text=_(
            'Should be something like "Cash", "Payable in 30 days", etc'
        ),
    )

    objects = ReceiptPDFManager()

    def _check_authorized(self):
        if not self.receipt.receipt_number:
            raise Exception(
                _('Cannot generate pdf for non-authorized receipt')
            )

    def save_pdf(self):
        """
        Save the receipt as a PDF related to this model.

        The related :class:`~.Receipt` should be validated first, of course.
        """
        self._check_authorized()

        with NamedTemporaryFile(suffix='.pdf') as file_:
            self.save_pdf_to(file_)
            self.pdf_file = File(file_, name='{}.pdf'.format(uuid.uuid4().hex))
            self.save()

    def save_pdf_to(self, file_):
        """
        Save the receipt as an actual PDF file into a custom location.

        The related :class:`~.Receipt` should be validated first, of course.
        """
        self._check_authorized()

        from . import pdf
        pdf.generate_receipt_pdf(self.receipt_id, file_)

    class Meta:
        verbose_name = _('receipt pdf')
        verbose_name_plural = _('receipt pdfs')


class ReceiptEntry(models.Model):
    """
    An entry in a receipt.

    Each ReceiptEntry represents a line in printable version of a Receipt. You
    should generally have one instance per product or service.

    Note that each entry has a :class:`~.Vat` because a single Receipt can have
    multiple products with different :class:`~.VatType`.
    """

    receipt = models.ForeignKey(
        Receipt,
        related_name='entries',
        verbose_name=_('receipt'),
    )
    description = models.CharField(
        max_length=128,
        verbose_name=_('description'),
    )
    quantity = models.PositiveSmallIntegerField(
        _('quantity'),
    )
    unit_price = models.DecimalField(
        _('unit price'),
        max_digits=15,
        decimal_places=2,
    )
    vat = models.ForeignKey(
        VatType,
        related_name='receipt_entries',
        verbose_name=_('vat'),
        null=True,
    )

    @property
    def total_price(self):
        """The total price for this line (quantity * price)."""
        return self.quantity * self.unit_price

    class Meta:
        verbose_name = _('receipt entry')
        verbose_name_plural = _('receipt entries')


class Tax(models.Model):
    """A tax (type+amount) for a specific Receipt."""

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
        """Auto-assign and return the total amount for this tax."""
        self.amount = self.base_amount * self.aliquot / 100
        return self.amount

    class Meta:
        verbose_name = _('tax')
        verbose_name_plural = _('taxes')


class Vat(models.Model):
    """A VAT (type+amount) for a specific Receipt."""

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

    class Meta:
        verbose_name = _('vat')
        verbose_name_plural = _('vat')


class Validation(models.Model):
    """
    The validation result for a batch.

    The validation result for an attempt to validate a batch. Note that each
    Receipt inside the batch will have its own :class:`~.ReceiptValidation`.
    """
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
    """
    An observation returned by AFIP.

    AFIP seems to assign re-used codes to Observation, so we actually store
    them as separate objects, and link to them from failed validations.
    """
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
    """
    The validation for a single :class:`~.Receipt`.

    This contains all validation-related data for a receipt, including its CAE
    and the CAE expiration, unless validation has failed.

    The ``observation`` field may contain any data returned by AFIP regarding
    validation failure.
    """

    validation = models.ForeignKey(
        Validation,
        verbose_name=_('validation'),
        related_name='receipts',
        help_text=_(
            'The validation for the batch that produced this instance.'
        ),
    )
    # TODO: replace this with a `successful` boolean field.
    result = models.CharField(
        _('result'),
        max_length=1,
        choices=(
            (Validation.RESULT_APPROVED, _('approved')),
            (Validation.RESULT_REJECTED, _('rejected')),
        ),
        help_text=_('Indicates whether the validation was succesful or not'),
    )
    cae = models.CharField(
        _('cae'),
        max_length=14,
        help_text=_('The CAE as returned by the AFIP'),
    )
    cae_expiration = models.DateField(
        _('cae expiration'),
        help_text=_('The CAE expiration as returned by the AFIP'),
    )
    observations = models.ManyToManyField(
        Observation,
        verbose_name=_('observations'),
        related_name='validations',
        help_text=_(
            'The observations as returned by the AFIP. These are generally '
            'present for failed validations.'
        ),
    )

    receipt = models.OneToOneField(
        Receipt,
        related_name='validation',
        verbose_name=_('receipt'),
        help_text=_('The Receipt for which this validation applies'),
    )

    class Meta:
        verbose_name = _('receipt validation')
        verbose_name_plural = _('receipt validations')
