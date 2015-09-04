from base64 import b64encode
from datetime import datetime, timedelta
from subprocess import Popen, PIPE
import logging
import random

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext as _
from lxml import etree
from lxml.builder import E
from suds import Client

logger = logging.getLogger(__name__)


endpoints = {}
if settings.AFIP_DEBUG:
    endpoints['wsaa'] = "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?wsdl"  # NOQA
    endpoints['wsfe'] = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL"
else:
    endpoints['wsaa'] = "https://wsaa.afip.gov.ar/ws/services/LoginCms?wsdl"
    endpoints['wsfe'] = "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL"  # NOQA


def format_date(date):
    """
    "Another date formatting function?" you're thinking, eh? Well, this
    actually formats dates in the *exact* format the AFIP's WS expects it,
    which is almost like ISO8601.

    Note that .isoformat() works fine on PROD, but not on TESTING.
    """
    return date.strftime("%Y-%m-%dT%H:%M:%S-00:00")


class GenericAfipTypeManager(models.Manager):

    def __init__(self, service_name):
        super().__init__()
        self.__service_name = service_name

    def populate(self):
        """
        Populates the database with valid types retrieved from AFIP's
        webservices.
        """
        pass  # TODO: Not Implemented!


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
    )
    valid_to = models.DateField(
        _('valid until'),
    )

    def __str__(self):
        return self.description

    class Meta:
        abstract = True


class ReceiptType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposCbte')

    class Meta:
        verbose_name = _("receipt type")
        verbose_name_plural = _("receipt types")


class ConceptType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposConcepto')

    class Meta:
        verbose_name = _("concept type")
        verbose_name_plural = _("concept types")


class DocumentType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposDoc')

    class Meta:
        verbose_name = _("document type")
        verbose_name_plural = _("document types")


class VatType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposIva')

    class Meta:
        verbose_name = _("vat type")
        verbose_name_plural = _("vat types")


class TaxType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposTributos')

    class Meta:
        verbose_name = _("tax type")
        verbose_name_plural = _("tax types")


class CurrencyType(GenericAfipType):

    objects = GenericAfipTypeManager('FEParamGetTiposTiposMonedas')

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
        return AuthTicket(owner=self, service=service)

    def __str__(self):
        return str(self.cuit)

    class Meta:
        verbose_name = _("taxpayer")
        verbose_name_plural = _("taxpayers")


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
        verbose_name=_('owner'),
    )

    def __str__(self):
        return str(self.number)

    class Meta:
        verbose_name = _('point of sales')
        verbose_name_plural = _('points of sales')


class AuthTicket(models.Model):
    owner = models.ForeignKey(
        TaxPayer,
        verbose_name=_('owner'),
    )
    unique_id = models.IntegerField(
        _('unique id'),
    )
    generated = models.DateTimeField(
        _('generated'),
    )
    expires = models.DateTimeField(
        _('expires'),
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

    TOKEN_XPATH = "/loginTicketResponse/credentials/token"
    SIGN_XPATH = "/loginTicketResponse/credentials/sign"

    def __create_request_xml(self):
        request_xml = (
            E.loginTicketRequest(
                {'version': '1.0'},
                E.header(
                    E.uniqueId(str(self.unique_id)),
                    E.generationTime(self.generated),
                    E.expirationTime(self.expires),
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

    def __create_request(self):
        now = datetime.now()  # up to 24h old
        tomorrow = now + timedelta(hours=10)  # up to 24h in the future

        self.generated = format_date(now)
        self.expires = format_date(tomorrow)
        # Can be larger, but let's not waste on this:
        self.unique_id = random.randint(0, 2147483647)

        request = self.__create_request_xml()
        signed_request = self.__sign_request(request)
        return b64encode(signed_request).decode()

    def authenticate(self, save=True):
        client = Client(endpoints['wsaa'])
        request = self.__create_request()
        raw_response = client.service.loginCms(request)
        response = etree.fromstring(raw_response.encode('utf-8'))

        self.token = response.xpath(self.TOKEN_XPATH)[0].text
        self.signature = response.xpath(self.SIGN_XPATH)[0].text
        if save:
            self.save()

    def __str__(self):
        return str(self.unique_id)

    class Meta:
        verbose_name = _('authorization ticket')
        verbose_name = _('authorization tickets')


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

    class Meta:
        verbose_name = _('receipt batch')
        verbose_name = _('receipt batches')


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
            'before validation is possible.'),
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
    vat_amount = models.DecimalField(
        _('vat amount'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Must be equal to the sum of all Vat objects.'),
    )
    tax_amount = models.DecimalField(
        _('tax amount'),
        max_digits=15,
        decimal_places=2,
        help_text=_('Must be equal to the sum of all Tax objects.'),
    )
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
    )
    related_receipts = models.ManyToManyField(
        'Receipt',
        _('related receipts'),
        blank=True,
    )

    # Not implemented: optionals

    # TODO: methods to compute total, vat_amount and taxes_amount

    # These two values are stored in the receipt's batch. However, before the
    # receipt is assigned into a batch, this value should be used.
    receipt_type = models.ForeignKey(ReceiptType)
    point_of_sales = models.ForeignKey(PointOfSales)

    def __str__(self):
        return '{} #{}'.format(self.receipt_type, self.receipt_number)

    class Meta:
        verbose_name = _('receipt')
        verbose_name_plural = _('receipts')
        unique_together = (
            ('receipt_type', 'receipt_number',)
        )
        # TODO: index_together...


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

    receipt = models.ForeignKey(Receipt)

    class Meta:
        verbose_name = _('tax')
        verbose_name_plural = _('taxes')


class Vat(models.Model):
    vat_type = models.ForeignKey(
        VatType,
        verbose_name=_('vat type'),
    )
    base = models.DecimalField(
        _('base amount'),
        max_digits=15,
        decimal_places=2,
    )
    amount = models.DecimalField(
        _('amount'),
        max_digits=15,
        decimal_places=2,
    )

    receipt = models.ForeignKey(Receipt)

    class Meta:
        verbose_name = _('vat')
        verbose_name_plural = _('vat')


class Validation(models.Model):
    RESULT_APPROVED = 'A'
    RESULT_REJECTED = 'R'
    RESULT_PARTIAL = 'P'

    processed_date = models.DateField(
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
    cae_expiration = models.DateTimeField(
        _('cae expiration'),
    )
    observations = models.ForeignKey(
        Observation,
        verbose_name=_('observations'),
    )

    receipt = models.OneToOneField(
        Receipt,
        related_name='validation',
        verbose_name=_('receipt'),
    )

    class Meta:
        verbose_name = _('receipt validation')
        verbose_name_plural = _('receipt validations')
