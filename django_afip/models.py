from django.db import models
from django.utils.translation import ugettext as _


class GenericAfipType(models.Model):
    code = models.CharField(max_length=3)
    description = models.CharField(max_length=250)
    valid_from = models.DateField()
    valid_to = models.DateField()

    class Meta:
        abstract = True


class ReceiptType(GenericAfipType):

    class Meta:
        verbose_name = _("receipt type")
        verbose_name_plural = _("receipt types")


class ConceptType(GenericAfipType):

    class Meta:
        verbose_name = _("concept type")
        verbose_name_plural = _("concept types")


class DocumentType(GenericAfipType):

    class Meta:
        verbose_name = _("document type")
        verbose_name_plural = _("document types")


class VatType(GenericAfipType):

    class Meta:
        verbose_name = _("vat type")
        verbose_name_plural = _("vat types")


class TaxType(GenericAfipType):

    class Meta:
        verbose_name = _("tax type")
        verbose_name_plural = _("tax types")


class CurrencyType(GenericAfipType):

    class Meta:
        verbose_name = _("currency type")
        verbose_name_plural = _("currency types")


class TaxPayer(models.Model):
    name = models.CharField(max_length=32)
    key = models.FileField(
        null=True,
    )
    certificate = models.FileField(
        null=True,
    )
    cuit = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = _("taxpayer")
        verbose_name_plural = _("taxpayers")


class PointOfSales(models.Model):
    number = models.PositiveSmallIntegerField()
    issuance_type = models.CharField(max_length=8)  # FIXME
    blocked = models.BooleanField()
    drop_date = models.DateField()

    owner = models.ForeignKey(TaxPayer)

    class Meta:
        verbose_name = _('point of sales')
        verbose_name_plural = _('points of sales')


class ReceiptBatch(models.Model):
    """
    Receipts are validated sent in batches.
    """

    receipt_type = models.ForeignKey(ReceiptType)
    point_of_sales = models.ForeignKey(PointOfSales)

    owner = models.ForeignKey(TaxPayer)

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
        related_name='details',
        null=True,
    )
    concept = models.ForeignKey(
        ConceptType,
        related_name='receipts',
    )
    document_type = models.ForeignKey(
        DocumentType,
        related_name='receipts',
    )
    document_number = models.BigIntegerField()
    # NOTE: WS will expect receipt_from and receipt_to.
    receipt_number = models.PositiveIntegerField(
        null=True,
    )
    date = models.DateField()
    net_untaxed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    net_taxed = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    exempt_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    service_from_date = models.DateField()
    service_to_date = models.DateField()
    expiration_date = models.DateField()
    currency = models.ForeignKey(
        CurrencyType,
        related_name='documents',
    )
    currency_quote = models.DecimalField(
        max_digits=10,
        decimal_places=6,
    )
    related_receipts = models.ManyToManyField(
        'Receipt',
    )

    # Not implemented: optionals

    # These two values are stored in the receipt's batch. However, before the
    # receipt is assigned into a batch, this value should be used.
    receipt_type = models.ForeignKey(ReceiptType)
    point_of_sales = models.ForeignKey(PointOfSales)

    @property
    def total(self):
        pass

    class Meta:
        verbose_name = _('receipt')
        verbose_name_plural = _('receipts')


class Tax(models.Model):
    tax_type = models.ForeignKey(TaxType)
    description = models.CharField(max_length=80)
    base_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    aliquot = models.DecimalField(
        max_digits=5,
        decimal_places=2,
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )

    receipt = models.ForeignKey(Receipt)

    class Meta:
        verbose_name = _('tax')
        verbose_name_plural = _('taxes')


class Vat(models.Model):
    vat_type = models.ForeignKey(VatType)
    base = models.DecimalField(
        max_digits=15,
        decimal_places=2,
    )
    amount = models.DecimalField(
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

    processed_date = models.DateField()
    result = models.CharField(
        max_length=1,
        choices=(
            (RESULT_APPROVED, _('approved')),
            (RESULT_REJECTED, _('rejected')),
            (RESULT_PARTIAL, _('partial')),
        ),
    )

    batch = models.ForeignKey(
        ReceiptBatch,
        related_name='validations'
    )

    class Meta:
        verbose_name = _('validation')
        verbose_name_plural = _('validations')


class Observation(models.Model):
    code = models.PositiveSmallIntegerField()
    message = models.CharField(max_length=255)

    class Meta:
        verbose_name = _('observation')
        verbose_name_plural = _('observations')


class ReceiptValidation(models.Model):
    validation = models.ForeignKey(Validation)
    result = models.CharField(
        max_length=1,
        choices=(
            (Validation.RESULT_APPROVED, _('approved')),
            (Validation.RESULT_REJECTED, _('rejected')),
            (Validation.RESULT_PARTIAL, _('partial')),
        ),
    )
    cae = models.CharField(max_length=14)
    cae_expiration = models.DateTimeField()
    observations = models.ForeignKey(Observation)

    receipt = models.ForeignKey(
        Receipt,
        related_name='validations',
    )

    class Meta:
        verbose_name = _('receipt validation')
        verbose_name_plural = _('receipt validations')
