from django.db import models


class GenericAfipType(models.Model):
    code = models.CharField(max_length=3)
    description = models.CharField(max_length=250)
    valid_from = models.DateField()
    valid_to = models.DateField()

    class Meta:
        abstract = True


class ReceiptType(GenericAfipType):
    pass


class ConceptType(GenericAfipType):
    pass


class DocumentType(GenericAfipType):
    pass


class VatType(GenericAfipType):
    pass


class TaxType(GenericAfipType):
    pass


class CurrencyType(GenericAfipType):
    pass


class TaxPayer(models.Model):
    name = models.CharField(max_length=32)
    key = models.FileField(
        null=True,
    )
    certificate = models.FileField(
        null=True,
    )
    cuit = models.PositiveSmallIntegerField()


class PointOfSales(models.Model):
    number = models.PositiveSmallIntegerField()
    issuance_type = models.CharField(max_length=8)  # FIXME
    blocked = models.BooleanField()
    drop_date = models.DateField()

    owner = models.ForeignKey(TaxPayer)


class ReceiptBatch(models.Model):
    """
    Receipts are validated sent in batches.
    """

    receipt_type = models.ForeignKey(ReceiptType)
    point_of_sales = models.ForeignKey(PointOfSales)

    owner = models.ForeignKey(TaxPayer)


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


class Validation(models.Model):
    RESULT_APPROVED = 'A'
    RESULT_REJECTED = 'R'
    RESULT_PARTIAL = 'P'

    processed_date = models.DateField()
    result = models.CharField(
        max_length=1,
        choices=(
            (RESULT_APPROVED, 'Aprovado'),
            (RESULT_REJECTED, 'Rechazado'),
            (RESULT_PARTIAL, 'Parcial'),
        ),
    )

    batch = models.ForeignKey(
        ReceiptBatch,
        related_name='validations'
    )


class Observation(models.Model):
    code = models.PositiveSmallIntegerField()
    message = models.CharField(max_length=255)


class ReceiptValidation(models.Model):
    validation = models.ForeignKey(Validation)
    result = models.CharField(
        max_length=1,
        choices=(
            (Validation.RESULT_APPROVED, 'Aprovado'),
            (Validation.RESULT_REJECTED, 'Rechazado'),
            (Validation.RESULT_PARTIAL, 'Parcial'),
        ),
    )
    cae = models.CharField(max_length=14)
    cae_expiration = models.DateTimeField()
    observations = models.ForeignKey(Observation)

    receipt = models.ForeignKey(
        Receipt,
        related_name='validations',
    )
