from datetime import date
from datetime import datetime
from pathlib import Path

from django.contrib.auth.models import User
from django.utils.timezone import make_aware
from factory import LazyFunction
from factory import PostGenerationMethodCall
from factory import Sequence
from factory import SubFactory
from factory import post_generation
from factory.django import DjangoModelFactory
from factory.django import FileField
from factory.django import ImageField

from django_afip import models


def get_test_file(filename: str, mode="r") -> Path:
    """Helper to get test files."""
    return Path(__file__).parent / "testing" / filename


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = "john doe"
    email = "john@doe.co"
    password = PostGenerationMethodCall("set_password", "123")


class SuperUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class ConceptTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.ConceptType
        django_get_or_create = ("code",)

    code = "1"
    description = "Producto"
    valid_from = date(2010, 9, 17)


class DocumentTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.DocumentType

    code = "96"
    description = "DNI"
    valid_from = date(2008, 7, 25)


class CurrencyTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.CurrencyType

    code = "PES"
    description = "Pesos Argentinos"
    valid_from = date(2009, 4, 3)


class ReceiptTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.ReceiptType
        django_get_or_create = ("code",)

    code = "11"
    description = "Factura C"
    valid_from = date(2011, 3, 30)


class TaxPayerFactory(DjangoModelFactory):
    class Meta:
        model = models.TaxPayer
        django_get_or_create = ["cuit"]

    name = "John Smith"
    cuit = 20329642330
    is_sandboxed = True
    key = FileField(from_path=get_test_file("test.key"))
    certificate = FileField(from_path=get_test_file("test.crt"))
    active_since = datetime(2011, 10, 3)
    logo = ImageField(from_path=get_test_file("tiny.png", "rb"))


class AlternateTaxpayerFactory(DjangoModelFactory):
    """A taxpayer with an alternate (valid) keypair."""

    class Meta:
        model = models.TaxPayer

    name = "John Smith"
    cuit = 20329642330
    is_sandboxed = True
    key = FileField(from_path=get_test_file("test2.key"))
    certificate = FileField(from_path=get_test_file("test2.crt"))
    active_since = datetime(2011, 10, 3)


class PointOfSalesFactory(DjangoModelFactory):
    class Meta:
        model = models.PointOfSales
        django_get_or_create = ["owner", "number"]

    number = 1
    issuance_type = "CAE"
    blocked = False
    owner = SubFactory(TaxPayerFactory)
    # TODO: Renamethis to something more regional:
    issuing_name = "Red Company Inc."
    issuing_address = "100 Red Av\nRedsville\nUK"
    issuing_email = "billing@example.com"
    vat_condition = "Exempt"
    gross_income_condition = "Exempt"
    sales_terms = "Credit Card"


class ReceiptFactory(DjangoModelFactory):
    class Meta:
        model = models.Receipt

    concept = SubFactory(ConceptTypeFactory, code=1)
    document_type = SubFactory(DocumentTypeFactory, code=96)
    document_number = 203012345
    issued_date = LazyFunction(date.today)
    total_amount = 130
    net_untaxed = 0
    net_taxed = 100
    exempt_amount = 0
    currency = SubFactory(CurrencyTypeFactory, code="PES")
    currency_quote = 1
    receipt_type = SubFactory(ReceiptTypeFactory, code=6)
    point_of_sales = SubFactory(PointOfSalesFactory)


class ReceiptWithVatAndTaxFactory(ReceiptFactory):
    """Receipt with a valid Vat and Tax, ready to validate."""

    point_of_sales = LazyFunction(lambda: models.PointOfSales.objects.first())

    @post_generation
    def post(obj: models.Receipt, create, extracted, **kwargs):
        VatFactory(vat_type__code=5, receipt=obj)
        TaxFactory(tax_type__code=3, receipt=obj)


class ReceiptFCEAWithVatAndTaxFactory(ReceiptFactory):
    """Receipt FCEA with a valid Vat and Tax, ready to validate."""

    document_number = 20111111112
    point_of_sales = LazyFunction(lambda: models.PointOfSales.objects.first())
    receipt_type = SubFactory(ReceiptTypeFactory, code=201)
    document_type = SubFactory(DocumentTypeFactory, code=80)
    expiration_date = LazyFunction(date.today)

    @post_generation
    def post(obj: models.Receipt, create, extracted, **kwargs):
        VatFactory(vat_type__code=5, receipt=obj)
        TaxFactory(tax_type__code=3, receipt=obj)


class ReceiptFCEAWithVatTaxAndOptionalsFactory(ReceiptFCEAWithVatAndTaxFactory):
    """Receipt FCEA with a valid Vat, Tax and Optionals, ready to validate."""

    total_amount = 13_000_000
    net_untaxed = 0
    net_taxed = 10_000_000

    @post_generation
    def post(obj: models.Receipt, create, extracted, **kwargs):
        VatFactory(
            vat_type__code=5,
            receipt=obj,
            base_amount=10_000_000,
            amount=2_100_000,
        )
        TaxFactory(
            tax_type__code=3,
            receipt=obj,
            base_amount=10_000_000,
            aliquot=9,
            amount=900_000,
        )
        OptionalFactory(optional_type__code=2101, receipt=obj)
        # Value SCA stands for TRANSFERENCIA AL SISTEMA DE CIRCULACION ABIERTA
        OptionalFactory(optional_type__code=27, receipt=obj, value="SCA")


class ReceiptWithInconsistentVatAndTaxFactory(ReceiptWithVatAndTaxFactory):
    """Receipt with a valid Vat and Tax, ready to validate."""

    document_type = SubFactory(DocumentTypeFactory, code=80)

    @post_generation
    def post(obj: models.Receipt, create, extracted, **kwargs):
        VatFactory(vat_type__code=5, receipt=obj)
        TaxFactory(tax_type__code=3, receipt=obj)


class ReceiptWithApprovedValidation(ReceiptFactory):
    """Receipt with fake (e.g.: not live) approved validation."""

    receipt_number = Sequence(lambda n: n + 1)

    @post_generation
    def post(obj: models.Receipt, create, extracted, **kwargs):
        ReceiptValidationFactory(receipt=obj)


class ReceiptValidationFactory(DjangoModelFactory):
    class Meta:
        model = models.ReceiptValidation

    result = models.ReceiptValidation.RESULT_APPROVED
    processed_date = make_aware(datetime(2017, 7, 2, 21, 6, 4))
    cae = "67190616790549"
    cae_expiration = make_aware(datetime(2017, 7, 12))
    receipt = SubFactory(ReceiptFactory, receipt_number=17)


class ReceiptPDFFactory(DjangoModelFactory):
    class Meta:
        model = models.ReceiptPDF

    client_address = "La Rioja 123\nX5000EVX Córdoba"
    client_name = "John Doe"
    client_vat_condition = "Consumidor Final"
    gross_income_condition = "Convenio Multilateral"
    issuing_address = "Happy Street 123, CABA"
    issuing_name = "Alice Doe"
    receipt = SubFactory(ReceiptFactory)
    sales_terms = "Contado"
    vat_condition = "Responsable Monotributo"


class ReceiptPDFWithFileFactory(ReceiptPDFFactory):
    receipt = SubFactory(ReceiptWithApprovedValidation)


class GenericAfipTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.GenericAfipType

    code = 80
    description = "CUIT"
    valid_from = datetime(2017, 8, 10)


class VatTypeFactory(GenericAfipTypeFactory):
    class Meta:
        model = models.VatType

    code = 5
    description = "21%"


class TaxTypeFactory(GenericAfipTypeFactory):
    class Meta:
        model = models.TaxType


class OptionalTypeFactory(GenericAfipTypeFactory):
    class Meta:
        model = models.OptionalType

    code = 2101
    description = "Excepcion computo IVA Credito Fiscal"


class VatFactory(DjangoModelFactory):
    class Meta:
        model = models.Vat

    amount = 21
    base_amount = 100
    receipt = SubFactory(ReceiptFactory)
    vat_type = SubFactory(VatTypeFactory)


class TaxFactory(DjangoModelFactory):
    class Meta:
        model = models.Tax

    aliquot = 9
    amount = 9
    base_amount = 100
    description = "Test description"
    receipt = SubFactory(ReceiptFactory)
    tax_type = SubFactory(TaxTypeFactory)


class OptionalFactory(DjangoModelFactory):
    class Meta:
        model = models.Optional

    # This value represent a valid CBU
    value = "1064169911100089878669"
    receipt = SubFactory(ReceiptFactory)
    optional_type = SubFactory(OptionalTypeFactory)


class ReceiptEntryFactory(DjangoModelFactory):
    class Meta:
        model = models.ReceiptEntry

    receipt = SubFactory(ReceiptFactory)
    description = "Test Entry"
    vat = SubFactory(VatTypeFactory)
