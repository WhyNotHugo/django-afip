from datetime import date, datetime

from factory import SubFactory
from factory.django import DjangoModelFactory

from django_afip import models


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
    cuit = '20329642330'
    is_sandboxed = True


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
