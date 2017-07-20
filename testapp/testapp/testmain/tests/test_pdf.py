from django.test import TestCase

from django_afip import models
from django_afip.pdf import ReceiptBarcodeGenerator
from testapp.testmain import fixtures


class ReceiptPDFGenerationTestCase(TestCase):
    def test_pdf_generation(self):
        """
        Test PDF file generation.

        For the moment, this test case mostly verifies that pdf generation
        *works*, but does not actually validate the pdf file itself.

        Running this locally *will* yield the file itself, which is useful for
        manual inspection.
        """
        pdf = fixtures.ReceiptPDFFactory(receipt__receipt_number=3)
        pdf.save_pdf()
        self.assertTrue(pdf.pdf_file.name.startswith('receipts/'))
        self.assertTrue(pdf.pdf_file.name.endswith('.pdf'))

    def test_unauthorized_receipt_generation(self):
        """
        Test PDF file generation for unauthorized receipts.

        Confirm that attempting to generate a PDF for an unauthorized receipt
        raises.
        """
        taxpayer = fixtures.TaxPayerFactory()
        fixtures.TaxPayerProfileFactory(taxpayer=taxpayer)
        receipt = fixtures.ReceiptFactory(
            receipt_number=None,
            point_of_sales__owner=taxpayer,
        )
        pdf = models.ReceiptPDF.objects.create_for_receipt(
            receipt=receipt,
            client_name='John Doe',
            client_address='12 Green Road\nGreenville\nUK',
        )
        with self.assertRaisesMessage(
            Exception,
            'Cannot generate pdf for non-authorized receipt'
        ):
            pdf.save_pdf()


class BarcodeGeneratorTestCase(TestCase):
    def assert_verification_digit(self, number, digit):
        number = [int(n) for n in number]
        self.assertEqual(
            ReceiptBarcodeGenerator.verification_digit(number),
            digit,
        )

    def test_verfification_digit(self):
        self.assert_verification_digit('01234567890', 5)
        self.assert_verification_digit(
            '123456789012345678901234567890123456789',
            0,
        )
        self.assert_verification_digit(
            '111111111112233334444444444444455555555',
            3,
        )
        self.assert_verification_digit(
            '202468793631100026719363618010820170512',
            9
        )
