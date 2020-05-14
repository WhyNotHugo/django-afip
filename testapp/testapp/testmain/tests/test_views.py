from datetime import date

import pytest
from django.test import Client
from django.test import TestCase
from django.urls import reverse

from django_afip import factories
from django_afip import views


class ReceiptPDFTestCase(TestCase):
    def test_html_view(self):
        """Test the HTML generation view."""
        pdf = factories.ReceiptPDFFactory(
            receipt__concept__code=1,
            receipt__issued_date=date(2017, 5, 15),
            receipt__receipt_type__code=11,
            receipt__point_of_sales__owner__logo=None,
        )
        factories.ReceiptValidationFactory(receipt=pdf.receipt)

        client = Client()
        response = client.get(
            "{}?html=true".format(
                reverse("receipt_displaypdf_view", args=(pdf.receipt.pk,))
            )
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
        <div class="qrcode">
          <img src="data:image/png;base64,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">
        </div>

        <p class="cae">
          <strong>CAE</strong>
          67190616790549
          <strong>Vto CAE</strong>
          July 12, 2017
        </p>

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

        client = Client()
        response = client.get(
            "{}?html=true".format(
                reverse("receipt_displaypdf_view", args=(pdf.receipt.pk,))
            )
        )

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
        response = client.get(reverse("receipt_pdf_view", args=(pdf.receipt.pk,)))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content[:7], b"%PDF-1.")

        headers = sorted(response.serialize_headers().decode().splitlines())
        self.assertIn("Content-Type: application/pdf", headers)


@pytest.mark.django_db
def test_template_discovery(client):
    taxpayer = factories.TaxPayerFactory(cuit="20329642330")
    factories.TaxPayerProfileFactory(taxpayer=taxpayer)
    pdf = factories.ReceiptPDFFactory(
        receipt__point_of_sales__owner=taxpayer,
        receipt__point_of_sales__number=9999,
        receipt__receipt_type__code=6,
    )
    factories.ReceiptValidationFactory(receipt=pdf.receipt)

    client = Client()
    response = client.get(
        "{}?html=true".format(
            reverse("receipt_displaypdf_view", args=(pdf.receipt.pk,))
        )
    )

    assert response.content == b"This is a dummy template to test template discovery.\n"


class ReceiptPDFViewDownloadNameTestCase(TestCase):
    def test_download_name(self):
        factories.ReceiptFactory(pk=9, receipt_number=32)

        view = views.ReceiptPDFView()
        view.kwargs = {"pk": 9}

        self.assertEqual(view.get_download_name(), "0001-00000032.pdf")
