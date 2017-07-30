from django.test import Client, TestCase
from django.urls import reverse

from testapp.testmain import fixtures


class ReceiptPDFTestCase(TestCase):
    def test_html_view(self):
        """Test the HTML generation view."""
        pdf = fixtures.ReceiptPDFFactory()
        fixtures.ReceiptValidationFactory(receipt=pdf.receipt)

        client = Client()
        response = client.get(
            reverse('receipt_html_view', args=(pdf.receipt.pk,))
        )
        self.assertContains(
            response,
            '<div class="client">\n'
            '<strong>Facturado a:</strong><br>\n'
            'John Doe,\n'
            'DNI\n33445566<br>\n'
            '12 Green Road<br />Greenville<br />UK<br>\n'
            'Condición de IVA: <br>\n'
            'Condición de Pago: \n</div>',
            html=True,
        )

    def test_pdf_view(self):
        """
        Test the PDF generation view.
        """
        taxpayer = fixtures.TaxPayerFactory()

        fixtures.TaxPayerProfileFactory(taxpayer=taxpayer)
        pdf = fixtures.ReceiptPDFFactory(
            receipt__point_of_sales__owner=taxpayer,
        )
        fixtures.ReceiptValidationFactory(receipt=pdf.receipt)

        client = Client()
        response = client.get(
            reverse('receipt_pdf_view', args=(pdf.receipt.pk,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:10], b'%PDF-1.5\n%')

        headers = sorted(response.serialize_headers().decode().splitlines())
        self.assertIn('Content-Type: application/pdf', headers)
        self.assertIn(
            'Content-Disposition: attachment; '
            'filename=receipt {}.pdf'.format(pdf.receipt.pk),
            headers
        )
