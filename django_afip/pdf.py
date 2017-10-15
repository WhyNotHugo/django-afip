import logging
from io import BytesIO

from barcode import ITF
from barcode.writer import ImageWriter
from django.utils.functional import cached_property


logger = logging.getLogger(__name__)


class ImageWitoutTextWriter(ImageWriter):
    def _paint_text(self, xpos, ypos):
        pass


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
