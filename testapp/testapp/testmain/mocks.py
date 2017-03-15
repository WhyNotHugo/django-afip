from datetime import date
from tempfile import NamedTemporaryFile

from django.contrib.auth.models import User
from django.core.files.base import File

from django_afip import models


def taxpayer(key=None):
    taxpayer = models.TaxPayer.objects.create(
        name='Test Taxpayer',
        cuit=20329642330,
        is_sandboxed=True,
    )

    if key:
        with NamedTemporaryFile(suffix='.key') as file_:
            file_.write(key)
            taxpayer.key = File(file_, name='test.key')
            taxpayer.save()

    return taxpayer


def superuser():
    return User.objects.create_superuser('test', 'test@example.com', '123')


def receipt(
        document_type=96,
        with_tax=True,
        with_vat=True,
        receipt_type=6,
     ):
    """
    Return a dummy mocked-receipt.

    This function is here for convenience only and has no special magic other
    than creating a receipt with valid Vat and Tax attributes.
    """
    total_amount = 100
    if with_tax:
        total_amount += 9
    if with_vat:
        total_amount += 21
    receipt = models.Receipt.objects.create(
        concept=models.ConceptType.objects.get(code=1),
        document_type=models.DocumentType.objects.get(
            code=document_type,
        ),
        document_number='203012345',
        issued_date=date.today(),
        total_amount=total_amount,
        net_untaxed=0,
        net_taxed=100,
        exempt_amount=0,
        currency=models.CurrencyType.objects.get(code='PES'),
        currency_quote=1,

        receipt_type=models.ReceiptType.objects.get(code=receipt_type),
        point_of_sales=models.PointOfSales.objects.first(),
    )
    if with_vat:
        models.Vat.objects.create(
            vat_type=models.VatType.objects.get(code=5),
            base_amount=100,
            amount=21,
            receipt=receipt,
        )
    if with_tax:
        models.Tax.objects.create(
            tax_type=models.TaxType.objects.get(code=3),
            base_amount=100,
            aliquot=9,
            amount=9,
            receipt=receipt,
        )
    return receipt
