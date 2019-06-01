from datetime import date

from django.test import Client, TestCase
from django.urls import reverse

from django_afip import factories, views


class ReceiptPDFTestCase(TestCase):
    def test_html_view(self):
        """Test the HTML generation view."""
        pdf = factories.ReceiptPDFFactory(
            receipt__concept__code=1,
            receipt__issued_date=date(2017, 5, 15),
            receipt__receipt_type__code=11,
        )
        factories.ReceiptValidationFactory(receipt=pdf.receipt)

        client = Client()
        response = client.get('{}?html=true'.format(
            reverse('receipt_displaypdf_view', args=(pdf.receipt.pk,))
        ))

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
            John Doe, DNI 203012345<br>
            La Rioja 123<br />X5000EVX Córdoba<br>
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
            <td>130.00</td>
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

    def test_logo_in_html(self):
        """Test the HTML generation view."""
        pdf = factories.ReceiptPDFFactory()
        factories.ReceiptValidationFactory(receipt=pdf.receipt)
        factories.TaxPayerExtras(taxpayer=pdf.receipt.point_of_sales.owner)

        client = Client()
        response = client.get('{}?html=true'.format(
            reverse('receipt_displaypdf_view', args=(pdf.receipt.pk,))
        ))

        self.assertContains(
            response,
            """
            <address>
            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAACXBIWXMAAAsTAAALEwEAmpwYAAAAB3RJTUUH4QgLERgyoZWu2QAAAB1pVFh0Q29tbWVudAAAAAAAQ3JlYXRlZCB3aXRoIEdJTVBkLmUHAAAAEklEQVQI12P4//8/AwT8//8fACnkBft7DmIIAAAAAElFTkSuQmCC" alt="Logo"><br>
            <strong>Alice Doe</strong><br>
            Happy Street 123, CABA<br>

            Responsable Monotributo<br>
            </address>
            """,  # noqa: E501: It's just long stuff. :(
            html=True,
        )

    def test_pdf_view(self):
        """
        Test the PDF generation view.
        """
        taxpayer = factories.TaxPayerFactory()

        factories.TaxPayerProfileFactory(taxpayer=taxpayer)
        pdf = factories.ReceiptPDFFactory(
            receipt__point_of_sales__owner=taxpayer,
        )
        factories.ReceiptValidationFactory(receipt=pdf.receipt)

        client = Client()
        response = client.get(
            reverse('receipt_pdf_view', args=(pdf.receipt.pk,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:7], b'%PDF-1.')

        headers = sorted(response.serialize_headers().decode().splitlines())
        self.assertIn('Content-Type: application/pdf', headers)


class ReceiptPDFViewDownloadNameTestCase(TestCase):
    def test_download_name(self):
        factories.ReceiptFactory(pk=9, receipt_number=32)

        view = views.ReceiptPDFView()
        view.kwargs = {'pk': 9}

        self.assertEqual(view.get_download_name(), '0001-00000032.pdf')
