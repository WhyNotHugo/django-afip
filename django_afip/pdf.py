import base64
import json
import logging
from io import BytesIO

import qrcode
from PIL import Image

from django_afip.models import Receipt

logger = logging.getLogger(__name__)


class ReceiptQrCode:
    # Note: There's a space in the middle in the docs.
    # I'm assuming it's a human error and that the URL doesn't take a space.
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
            "cuit": str(receipt.point_of_sales.owner.cuit),
            "ptoVta": receipt.point_of_sales.number,
            "tipoCmp": receipt.receipt_type.code,
            "nroCmp": receipt.receipt_number,
            "importe": float(receipt.total_amount),
            "moneda": receipt.currency.code,
            "ctz": float(receipt.currency_quote),
            "tipoDocRec": receipt.document_type.code,
            "nroDocRec": receipt.document_number,
            "tipoCodAut": "E",  # We don't support anything except CAE.
            "codAut": receipt.validation.cae,
        }

    def as_png(self) -> Image:
        json_data = json.dumps(self._data)
        encoded_json = base64.b64encode(json_data.encode()).decode()
        url = f"{self.BASE_URL}{encoded_json}"

        qr = qrcode.QRCode(version=1, border=4)
        qr.add_data(url)
        qr.make()

        return qr.make_image()


def get_encoded_qrcode(receipt_pdf) -> str:
    """Return a QRCode encoded for embeding in HTML."""

    img_data = BytesIO()
    qr_img = ReceiptQrCode(receipt_pdf.receipt).as_png()
    qr_img.save(img_data, format="PNG")

    return base64.b64encode(img_data.getvalue()).decode()
