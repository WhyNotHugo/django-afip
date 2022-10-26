import re
from datetime import date

import pytest

from django_afip import factories
from django_afip import models
from django_afip.pdf import ReceiptQrCode


@pytest.mark.django_db
def test_pdf_generation():
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


@pytest.mark.django_db
def test_unauthorized_receipt_generation():
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


@pytest.mark.django_db
def test_signal_generation_for_not_validated_receipt():
    printable = factories.ReceiptPDFFactory()

    assert not (printable.pdf_file)


@pytest.mark.django_db
def test_signal_generation_for_validated_receipt():
    validation = factories.ReceiptValidationFactory()
    printable = factories.ReceiptPDFFactory(receipt=validation.receipt)

    assert printable.pdf_file
    assert printable.pdf_file.name.endswith(".pdf")


@pytest.mark.django_db
def test_qrcode_data():
    pdf = factories.ReceiptPDFFactory(
        receipt__receipt_number=3,
        receipt__issued_date=date(2021, 3, 2),
    )
    factories.ReceiptValidationFactory(receipt=pdf.receipt)

    qrcode = ReceiptQrCode(pdf.receipt)
    assert qrcode._data == {
        "codAut": "67190616790549",
        "ctz": 1.0,
        "cuit": "20329642330",
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


# --------------------------------------------
@pytest.mark.django_db
def test_pdf_generation_caea():
    """Test PDF file generation.

    For the moment, this test case mostly verifies that pdf generation
    *works*, but does not actually validate the pdf file itself.

    Running this locally *will* yield the file itself, which is useful for
    manual inspection.
    """
    caea = factories.CaeaFactory()
    pdf = factories.ReceiptPDFFactory(
        receipt=factories.ReceiptFactory(
            point_of_sales=factories.SubFactory(factories.PointOfSalesFactoryCaea)
        ),
        receipt__receipt_number=3,
    )
    factories.ReceiptValidationFactory(receipt=pdf.receipt)
    pdf.save_pdf()
    regex = r"afip/receipts/[a-f0-9]{2}/[a-f0-9]{2}/[a-f0-9]{32}.pdf"

    assert re.match(regex, pdf.pdf_file.name)
    assert pdf.pdf_file.name.endswith(".pdf")


@pytest.mark.django_db
def test_qrcode_data_caea():
    caea = factories.CaeaFactory()
    pos_caea = factories.PointOfSalesFactoryCaea()
    receipt = factories.ReceiptFactory(point_of_sales=pos_caea)
    pdf = factories.ReceiptPDFFactory(
        receipt=receipt,
    )
    factories.ReceiptValidationFactory(receipt=pdf.receipt, cae=caea.caea_code)

    qrcode = ReceiptQrCode(pdf.receipt)
    assert qrcode._data == {
        "codAut": int(caea.caea_code),
        "ctz": 1.0,
        "cuit": "20329642330",
        "fecha": str(date.today()),
        "importe": 130.0,
        "moneda": "PES",
        "nroCmp": receipt.receipt_number,
        "nroDocRec": receipt.document_number,
        "ptoVta": receipt.point_of_sales.number,
        "tipoCmp": receipt.receipt_type.code,
        "tipoCodAut": "E",
        "tipoDocRec": receipt.document_type.code,
        "ver": 1,
    }


@pytest.mark.django_db
def test_signal_generation_for_not_validated_receipt():
    caea = factories.CaeaFactory()
    pos = factories.PointOfSalesFactoryCaea()
    receipt = factories.ReceiptFactory(point_of_sales=pos)
    printable = factories.ReceiptPDFFactory(receipt=receipt)
    assert (
        printable.pdf_file
    )  # even if is not validated with CAEA must print make a PDF
    assert not receipt.is_validated


@pytest.mark.django_db
def test_signal_generation_for_not_validated_receipt():
    caea = factories.CaeaFactory()
    pos = factories.PointOfSalesFactoryCaea()
    receipt = factories.ReceiptFactory(point_of_sales=pos)
    validation = factories.ReceiptValidationFactory(receipt=receipt)

    printable = factories.ReceiptPDFFactory(receipt=receipt)
    assert printable.pdf_file
    assert receipt.is_validated
