from datetime import date

from django_afip import models


def receipt(
        document_type=96,
        with_tax=True,
        with_vat=True,
        receipt_type=6,
        document_number='203012345',
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
        document_number=document_number,
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
