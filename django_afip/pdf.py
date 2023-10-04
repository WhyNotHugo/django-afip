from __future__ import annotations

import base64
import json
import logging
from io import BytesIO
from typing import TYPE_CHECKING

import qrcode
from django.core.paginator import Paginator
from django_renderpdf.helpers import render_pdf
from typing import Sequence
from typing import TypedDict

if TYPE_CHECKING:
    from decimal import Decimal
    from typing import IO

    from PIL import Image

    from django_afip.models import Receipt
    from django_afip.models import ReceiptPDF
    from django_afip.models import ReceiptEntry


logger = logging.getLogger(__name__)


class ReceiptQrCode:
    """A QR code for receipt

    See: https://www.afip.gob.ar/fe/qr/especificaciones.asp"""

    BASE_URL = "https://www.afip.gob.ar/fe/qr/?p="

    def __init__(self, receipt: Receipt) -> None:
        self._receipt = receipt
        # The examples on the website say that "importe" and "ctz" are both "decimal"
        # type. JS/JSON has no decimal type. The examples use integeres.
        #
        # Using integers would drop cents, which would result in mismatching
        # information. Using strings would add quotes, which likely breaks.
        #
        # Using floats seems to be the only viable solution, and SHOULD be fine for
        # values in the range supported.
        self._data = {
            "ver": 1,
            "fecha": receipt.issued_date.strftime("%Y-%m-%d"),
            "cuit": receipt.point_of_sales.owner.cuit,
            "ptoVta": receipt.point_of_sales.number,
            "tipoCmp": int(receipt.receipt_type.code),
            "nroCmp": receipt.receipt_number,
            "importe": float(receipt.total_amount),
            "moneda": receipt.currency.code,
            "ctz": float(receipt.currency_quote),
            "tipoDocRec": int(receipt.document_type.code),
            "nroDocRec": receipt.document_number,
            "tipoCodAut": "E",  # TODO: need to implement CAEA
            "codAut": int(receipt.validation.cae),
        }

    def as_png(self) -> Image:
        json_data = json.dumps(self._data)
        encoded_json = base64.b64encode(json_data.encode()).decode()
        url = f"{self.BASE_URL}{encoded_json}"

        qr = qrcode.QRCode(version=1, border=4)
        qr.add_data(url)
        qr.make()

        return qr.make_image()


def get_encoded_qrcode(receipt_pdf: ReceiptPDF) -> str:
    """Return a QRCode encoded for embeding in HTML."""

    img_data = BytesIO()
    qr_img = ReceiptQrCode(receipt_pdf.receipt).as_png()
    qr_img.save(img_data, format="PNG")

    return base64.b64encode(img_data.getvalue()).decode()


# Note: When updating this, be sure to update the docstring of the method that uses
# these below.
TEMPLATE_NAMES = [
    "receipts/{taxpayer}/pos_{point_of_sales}/code_{code}.html",
    "receipts/{taxpayer}/code_{code}.html",
    "receipts/code_{code}.html",
    "receipts/{code}.html",
]

class EntriesForPage(TypedDict):
    previous_subtotal: Decimal
    subtotal: Decimal
    entries: Sequence[ReceiptEntry]


def create_entries_context_for_render(
    paginator: Paginator,
) -> dict[int, EntriesForPage]:
    entries = {}
    subtotal = 0
    for i in paginator.page_range:
        entries[i] = {}
        entries[i]["previous_subtotal"] = subtotal
        page = paginator.get_page(i)
        for entry in page.object_list:
            subtotal += round(entry.total_price, 2)

        entries[i]["subtotal"] = subtotal
        entries[i]["entries"] = paginator.get_page(i).object_list
    return entries


class PdfBuilder:
    """Builds PDF files for Receipts.

    Creating a new instance of a builder does nothing; use :meth:`~render_pdf` to
    actually render the file.

    This type can be subclassed to add custom behaviour or data into PDF files.
    """

    def __init__(self, entries_per_page: int = 15) -> None:
        self.entries_per_page = entries_per_page

    def get_template_names(self, receipt: Receipt) -> list[str]:
        """Return the templates use to render the Receipt PDF.

        Template discovery tries to find any of the below receipts::

            receipts/{taxpayer}/pos_{point_of_sales}/code_{code}.html
            receipts/{taxpayer}/code_{code}.html
            receipts/code_{code}.html
            receipts/{code}.html

        To override, for example, the "Factura C" template for point of sales 0002 for
        Taxpayer 20-32964233-0, use::

            receipts/20329642330/pos_2/code_6.html
        """
        return [
            template.format(
                taxpayer=receipt.point_of_sales.owner.cuit,
                point_of_sales=receipt.point_of_sales.number,
                code=receipt.receipt_type.code,
            )
            for template in TEMPLATE_NAMES
        ]

    def get_context(self, receipt: Receipt) -> dict:
        """Returns the context used to render the PDF file."""
        from django_afip.models import Receipt
        from django_afip.models import ReceiptPDF

        context: dict = {}

        receipt_pdf = (
            ReceiptPDF.objects.select_related(
                "receipt",
                "receipt__receipt_type",
                "receipt__document_type",
                "receipt__validation",
                "receipt__point_of_sales",
                "receipt__point_of_sales__owner",
            )
            .prefetch_related(
                "receipt__entries",
            )
            .get(receipt=receipt)
        )

        # Prefetch required data in a single query:
        receipt_pdf.receipt = (
            Receipt.objects.select_related(
                "receipt_type",
                "document_type",
                "validation",
                "point_of_sales",
                "point_of_sales__owner",
            )
            .prefetch_related(
                "entries",
            )
            .get(
                pk=receipt_pdf.receipt_id,
            )
        )
        taxpayer = receipt_pdf.receipt.point_of_sales.owner
        paginator = Paginator(receipt_pdf.receipt.entries.all(), self.entries_per_page)

        context["entries"] = create_entries_context_for_render(paginator)
        context["pdf"] = receipt_pdf
        context["taxpayer"] = taxpayer
        context["qrcode"] = get_encoded_qrcode(receipt_pdf)

        return context

    def render_pdf(self, receipt: Receipt, file_: IO) -> None:
        """Renders the PDF into ``file_``."""
        render_pdf(
            template=self.get_template_names(receipt),
            file_=file_,
            context=self.get_context(receipt),
        )
