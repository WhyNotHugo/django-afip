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


class SalesPoint(models.Model):
    number = models.PositiveSmallIntegerField()
    issuance_type = models.CharField(max_length=8)  # FIXME
    blocked = models.BooleanField()
    drop_date = models.DateField()


class Credentials(models.Model):
    name = models.CharField(max_length=32)
    key = models.FieldField(
        null=True,
    )
    certificate = models.FieldField(
        null=True,
    )


class ReceiptBatch(models.Model):
    """
    Receipts are validated sent in batches.
    """

    amount = models.PositiveSmallIntegerField()
    receipt_type = models.ForeignKey(ReceiptType)
    sales_point = models.ForeignKey(SalesPoint)


class Receipt(models.Model):
    """
    An AFIP-related document (eg: invoice).
    """
    pack = models.ForeignKey(
        ReceiptBatch,
        related_name='details',
        null=True,
    )
    concept = models.ForeignKey(
        ConceptType,
        related_name='documents',
    )
    document_type = models.ForeignKey(
        DocumentType,
        related_name='documents',
    )
    document_number = models.BigIntegerField()
    from_invoice = models.PositiveIntegerField(
        null=True,
    )
    to_invoice = models.PositiveIntegerField(
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

    # optionals

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
