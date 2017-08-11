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

        self.assertHTMLEqual(
            response.content.decode(),
            """
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="/static/receipts/receipt.css">
  </head>
  <body>
    <div class="receipt">

      <header>
        <div class="taxpayer-details group">
          <address>
            <strong>Alice Doe</strong><br>
            Happy Street 123, CABA<br>

            Responsable Monotributo<br>
          </address>

          <div class="receipt-type">
            <div class="identifier">
              C
            </div>
            <div class="code">
              Código 11
            </div>
          </div>

          <div class="receipt-details">
            <div class="receipt-type-description">
              Factura C
            </div>
            <strong>Nº</strong> None
            <br>
            <strong>Fecha de emisión:</strong> <time>May 15, 2017</time><br>
            <strong>CUIT:</strong> 20-32964233-0<br>
            <strong>Ingresos Brutos:</strong> Convenio Multilateral<br>
            <strong>Inicio de Actividades:</strong> Oct. 3, 2011
          </div>
        </div>

        <hr>

        <div class="client">
          <div><strong>Facturado a:</strong></div>
          <div class="sale-conditions">
            <strong>Condición de IVA:</strong> Consumidor Final<br>
            <strong>Condición de Pago:</strong> Contado
          </div>
          <div class="client-data">
            John Doe,
            DNI
            33445566<br>
            La Rioja 123<br />X5000EVX Córdoba<br>
          </div>
        </div>

        <hr>
        <div class="service-dates">
          <div>
            <strong>Periodo del servicio:</strong>
            None al None
          </div>
          <div class="expiration">
            <strong>Vencimiento:</strong> None
          </div>
        </div>

      </header>

      <hr>

      <table>
        <thead>
          <tr>
            <th>Descripción</th>
            <th>Cantidad</th>
            <th>Precio Unitario</th>
            <th>Monto</th>
          </tr>
        </thead>
        <tbody>

        </tbody>
        <tfoot>
          <tr>
            <td></td>
            <td></td>
            <td></td>
            <td>100.00</td>
          </tr>
        </tfoot>
      </table>

      <footer>
        <p class="cae">
          <strong>CAE</strong>
          67190616790549
          <strong>Vto CAE</strong>
          July 12, 2017
        </p>

        <div class="barcode">
          <img src="data:image/png;base64,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">
        </div>

        Consultas de validez:
        <a href="http://www.afip.gob.ar/genericos/consultacae/">
          http://www.afip.gob.ar/genericos/consultacae/
        </a>
        <br>
        Teléfono Gratuito CABA, Área de Defensa y Protección al Consumidor.
        Tel 147
      </footer>

    </div>
  </body>
</html>
            """,  # noqa: E501: It's just long stuff. :(
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
