from __future__ import annotations

import random
import re
from datetime import date
from unittest.mock import patch

import pytest
from django.core.paginator import Paginator

from django_afip import factories
from django_afip import models
from django_afip.pdf import PdfBuilder
from django_afip.pdf import ReceiptQrCode
from django_afip.pdf import create_entries_context_for_render


@pytest.mark.django_db()
def test_pdf_generation() -> None:
    """Test PDF file generation.

    For the moment, this test case mostly verifies that pdf generation
    *works*, but does not actually validate the pdf file itself.

    Running this locally *will* yield the file itself, which is useful for
    manual inspection.
    """
    pdf = factories.ReceiptPDFFactory(receipt__receipt_number=3)
    factories.ReceiptValidationFactory(receipt=pdf.receipt)
    pdf.save_pdf()
    regex = r"afip/receipts/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{32}.pdf"

    assert re.match(regex, pdf.pdf_file.name)
    assert pdf.pdf_file.name.endswith(".pdf")


@pytest.mark.django_db()
def test_unauthorized_receipt_generation() -> None:
    """
    Test PDF file generation for unauthorized receipts.

    Confirm that attempting to generate a PDF for an unauthorized receipt
    raises.
    """
    taxpayer = factories.TaxPayerFactory()
    receipt = factories.ReceiptFactory(
        receipt_number=None,
        point_of_sales__owner=taxpayer,
    )
    pdf = models.ReceiptPDF.objects.create_for_receipt(
        receipt=receipt,
        client_name="John Doe",
        client_address="12 Green Road\nGreenville\nUK",
    )
    with pytest.raises(
        Exception, match="Cannot generate pdf for non-authorized receipt"
    ):
        pdf.save_pdf()


@pytest.mark.django_db()
def test_signal_generation_for_not_validated_receipt() -> None:
    printable = factories.ReceiptPDFFactory()

    assert not (printable.pdf_file)


@pytest.mark.django_db()
def test_qrcode_data() -> None:
    pdf = factories.ReceiptPDFFactory(
        receipt__receipt_number=3,
        receipt__issued_date=date(2021, 3, 2),
    )
    factories.ReceiptValidationFactory(receipt=pdf.receipt)

    qrcode = ReceiptQrCode(pdf.receipt)
    assert qrcode._data == {
        "codAut": 67190616790549,
        "ctz": 1.0,
        "cuit": 20329642330,
        "fecha": "2021-03-02",
        "importe": 130.0,
        "moneda": "PES",
        "nroCmp": 3,
        "nroDocRec": 203012345,
        "ptoVta": 1,
        "tipoCmp": 6,
        "tipoCodAut": "E",
        "tipoDocRec": 96,
        "ver": 1,
    }


@pytest.mark.django_db()
def test_create_entries_for_render() -> None:
    validation = factories.ReceiptValidationFactory()
    for _i in range(10):
        factories.ReceiptEntryFactory(
            receipt=validation.receipt, unit_price=1, quantity=1
        )
    entries_queryset = models.ReceiptEntry.objects.all()
    paginator = Paginator(entries_queryset, 5)
    entries = create_entries_context_for_render(paginator)

    assert list(entries.keys()) == [1, 2]
    assert entries[1]["previous_subtotal"] == 0
    assert entries[1]["subtotal"] == 5
    assert list(entries[1]["entries"]) == list(models.ReceiptEntry.objects.all()[:5])

    assert entries[2]["previous_subtotal"] == 5
    assert entries[2]["subtotal"] == 10
    assert list(entries[2]["entries"]) == list(models.ReceiptEntry.objects.all()[5:10])


@pytest.mark.django_db()
def test_receipt_pdf_modified_builder() -> None:
    validation = factories.ReceiptValidationFactory()
    validation.receipt.total_amount = 20
    validation.receipt.save()
    for _i in range(10):
        random.uniform(1.00, 12.5)
        factories.ReceiptEntryFactory(
            receipt=validation.receipt, unit_price=1, quantity=2
        )

    printable = factories.ReceiptPDFFactory(receipt=validation.receipt)
    assert not printable.pdf_file

    printable.save_pdf(builder=PdfBuilder(entries_per_page=5))
    assert printable.pdf_file
    assert printable.pdf_file.name.endswith(".pdf")


@pytest.mark.django_db()
def test_receipt_pdf_call_function() -> None:
    validation = factories.ReceiptValidationFactory()
    for _i in range(80):
        price = random.uniform(1.00, 12.5)
        factories.ReceiptEntryFactory(
            receipt=validation.receipt, unit_price=price, quantity=2
        )

    printable = factories.ReceiptPDFFactory(receipt=validation.receipt)
    with patch(
        "django_afip.pdf.create_entries_context_for_render", spec=True
    ) as mocked_call:
        printable.save_pdf(builder=PdfBuilder(entries_per_page=5))

    assert mocked_call.called
    assert mocked_call.call_count == 1
