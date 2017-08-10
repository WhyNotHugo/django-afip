import os
from datetime import date, datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.timezone import make_aware
from factory import PostGenerationMethodCall, SubFactory
from factory.django import DjangoModelFactory, FileField

from django_afip import models


def _key_file():
    return open(os.path.join(settings.BASE_DIR, 'test.key'))


def _cert_file():
    return open(os.path.join(settings.BASE_DIR, 'test.crt'))


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = 'john doe'
    email = 'john@doe.co'
    password = PostGenerationMethodCall('set_password', '123')


class SuperUserFactory(UserFactory):
    is_staff = True
    is_superuser = True


class ConceptTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.ConceptType

    code = '1'
    description = 'Producto'
    valid_from = date(2010, 9, 17)


class DocumentTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.DocumentType

    code = '96'
    description = 'DNI'
    valid_from = date(2008, 7, 25)


class CurrencyTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.CurrencyType

    code = 'PES'
    description = 'Pesos Argentinos'
    valid_from = date(2009, 4, 3)


class ReceiptTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.ReceiptType

    code = '11'
    description = 'Factura C'
    valid_from = date(2011, 3, 30)


class TaxPayerFactory(DjangoModelFactory):
    class Meta:
        model = models.TaxPayer

    name = 'John Smith'
    cuit = 20329642330
    is_sandboxed = True
    key = FileField(from_func=_key_file)
    certificate = FileField(from_func=_cert_file)
    active_since = datetime(2011, 10, 3)


class TaxPayerProfileFactory(DjangoModelFactory):
    class Meta:
        model = models.TaxPayerProfile

    taxpayer = SubFactory(TaxPayerFactory)
    issuing_name = 'Red Company Inc.'
    issuing_address = '100 Red Av\nRedsville\nUK'
    issuing_email = 'billing@example.com'
    vat_condition = 'Exempt'
    gross_income_condition = 'Exempt'
    sales_terms = 'Credit Card'


class PointOfSalesFactory(DjangoModelFactory):
    class Meta:
        model = models.PointOfSales

    number = 1
    issuance_type = 'CAE'
    blocked = False
    owner = SubFactory(TaxPayerFactory)


class ReceiptFactory(DjangoModelFactory):
    class Meta:
        model = models.Receipt

    concept = SubFactory(ConceptTypeFactory)
    document_type = SubFactory(DocumentTypeFactory)
    document_number = 33445566
    issued_date = datetime(2017, 5, 15)
    total_amount = 100
    net_untaxed = 0
    net_taxed = 100
    exempt_amount = 0
    currency = SubFactory(CurrencyTypeFactory)
    currency_quote = 1
    receipt_type = SubFactory(ReceiptTypeFactory)
    point_of_sales = SubFactory(PointOfSalesFactory)


class ReceiptValidationFactory(DjangoModelFactory):
    class Meta:
        model = models.ReceiptValidation

    result = models.ReceiptValidation.RESULT_APPROVED
    processed_date = make_aware(datetime(2017, 7, 2, 21, 6, 4))
    cae = '67190616790549'
    cae_expiration = make_aware(datetime(2017, 7, 12))
    receipt = SubFactory(ReceiptFactory, receipt_number=17)


class ReceiptPDFFactory(DjangoModelFactory):
    class Meta:
        model = models.ReceiptPDF

    receipt = SubFactory(ReceiptFactory)
    client_name = 'John Doe'
    client_address = '12 Green Road\nGreenville\nUK'


class GenericAfipTypeFactory(DjangoModelFactory):
    class Meta:
        model = models.GenericAfipType

    code = 80
    description = 'CUIT'
    valid_from = datetime(2017, 8, 10)


class VatTypeFactory(GenericAfipTypeFactory):
    class Meta:
        model = models.VatType


class TaxTypeFactory(GenericAfipTypeFactory):
    class Meta:
        model = models.TaxType


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
    receipt = SubFactory(ReceiptFactory)
    tax_type = SubFactory(TaxTypeFactory)
