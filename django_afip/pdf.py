import base64
import logging
import mimetypes
from io import BytesIO

from barcode import ITF
from barcode.writer import ImageWriter
from django.contrib.staticfiles.finders import find
from django.contrib.staticfiles.storage import staticfiles_storage
from django.template.loader import get_template
from django.utils.functional import cached_property
from weasyprint import default_url_fetcher, HTML

from . import models

logger = logging.getLogger(__name__)


class ImageWitoutTextWriter(ImageWriter):
    def _paint_text(self, xpos, ypos):
        pass


def staticfile_url_fetcher(url):
    """
    Returns files when the staticfiles app does not returns a relative path to
    a file.
    """
    if url.startswith('/'):
        base_url = staticfiles_storage.base_url
        filename = url.replace(base_url, '', 1)

        filepath = find(filename)
        with open(filepath, 'rb') as file_:
            data = file_.read()
        return {
            'string': data,
            'mime_type': mimetypes.guess_type(url)[0],
        }
    else:
        return default_url_fetcher(url)


def generate_receipt_pdf(pk, target, force_html=False):

    pdf = models.ReceiptPDF.objects.select_related(
        'receipt',
        'receipt__receipt_type',
        'receipt__document_type',
        'receipt__validation',
        'receipt__point_of_sales',
        'receipt__point_of_sales__owner',
    ).prefetch_related(
        'receipt__entries',
    ).get(
        receipt__pk=pk
    )

    generator = ReceiptBarcodeGenerator(pdf.receipt)
    barcode = base64.b64encode(generator.generate_barcode())

    html = get_template('receipts/code_{}.html'.format(
        pdf.receipt.receipt_type.code,
    )).render({
        'pdf': pdf,
        'taxpayer': pdf.receipt.point_of_sales.owner,
        'barcode': barcode,
    })

    if force_html:
        return html
    else:
        return HTML(
            string=html,
            base_url='not-used://',
            url_fetcher=staticfile_url_fetcher,
        ).write_pdf(
            target=target,
        )


class ReceiptBarcodeGenerator:
    def __init__(self, receipt):
        self._receipt = receipt

    @cached_property
    def numbers(self):
        """"
        Returns the barcode's number without the verification digit.

        :return: list(int)
        """
        numstring = '{:011d}{:02d}{:04d}{}{}'.format(
            self._receipt.point_of_sales.owner.cuit,  # 11 digits
            int(self._receipt.receipt_type.code),  # 2 digits
            self._receipt.point_of_sales.number,  # point of sales
            self._receipt.validation.cae,  # 14 digits
            self._receipt.validation.cae_expiration.strftime('%Y%m%d'),  # 8
        )
        return [int(num) for num in numstring]

    @staticmethod
    def verification_digit(numbers):
        """
        Returns the verification digit for a given numbre.

        The verification digit is calculated as follows:

        * A = sum of all even-positioned numbers
        * B = A * 3
        * C = sum of all odd-positioned numbers
        * D = B + C
        * The results is the smallset number N, such that (D + N) % 10 == 0

        NOTE: Afip's documentation seems to have odd an even mixed up in the
        explanation, but all examples follow the above algorithm.

        :param list(int) numbers): The numbers for which the digits is to be
            calculated.
        :return: int
        """
        a = sum(numbers[::2])
        b = a * 3
        c = sum(numbers[1::2])
        d = b + c
        e = d % 10
        if e == 0:
            return e
        return 10 - e

    @cached_property
    def full_number(self):
        """
        Returns the full number including the verification digit.

        :return: str
        """
        return '{}{}'.format(
            ''.join(str(n) for n in self.numbers),
            ReceiptBarcodeGenerator.verification_digit(self.numbers),
        )

    def generate_barcode(self, writer_class=ImageWitoutTextWriter):
        rv = BytesIO()
        ITF(self.full_number, writer=writer_class()).write(rv)

        return rv.getvalue()
