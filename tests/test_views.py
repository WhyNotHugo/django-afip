from __future__ import annotations

from datetime import date

import pytest
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from pytest_django.asserts import assertContains
from pytest_django.asserts import assertHTMLEqual

from django_afip import factories
from django_afip import views


class ReceiptPDFTestCase(TestCase):
    def test_html_view(self) -> None:
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

        assertHTMLEqual(
            response.content.decode(),
            """

<!DOCTYPE html>



<html>
  <head>
    <meta charset="utf-8">
    <link rel="stylesheet" href="/static/receipts/receipt.css">
  </head>
  <body>
    
    <div class="receipt" style="page-break-after: always;">

      <header class="page-header">
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
            203012345<br>
            La Rioja 123<br>X5000EVX Córdoba<br>
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

              <td>Total</td>
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
        <br>

        Hoja 1 de 1

      </footer>
    </div>

  </body>


</html>
""",  # noqa: E501: It's just long stuff. :(
        )

    def test_logo_in_html(self) -> None:
        """Test the HTML generation view."""
        pdf = factories.ReceiptPDFFactory()
        factories.ReceiptValidationFactory(receipt=pdf.receipt)

        client = Client()
        response = client.get(
            "{}?html=true".format(
                reverse("receipt_displaypdf_view", args=(pdf.receipt.pk,))
            )
        )

        assertContains(
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

    def test_pdf_view(self) -> None:
        """
        Test the PDF generation view.
        """
        taxpayer = factories.TaxPayerFactory()

        pdf = factories.ReceiptPDFFactory(
            receipt__point_of_sales__owner=taxpayer,
        )
        factories.ReceiptValidationFactory(receipt=pdf.receipt)

        client = Client()
        response = client.get(reverse("receipt_pdf_view", args=(pdf.receipt.pk,)))

        assert response.status_code == 200
        assert response.content[:7] == b"%PDF-1."

        headers = sorted(response.serialize_headers().decode().splitlines())
        assert "Content-Type: application/pdf" in headers


@pytest.mark.django_db()
def test_template_discovery(client: Client) -> None:
    taxpayer = factories.TaxPayerFactory(cuit="20329642330")
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
    def test_download_name(self) -> None:
        factories.ReceiptFactory(pk=9, receipt_number=32)

        view = views.ReceiptPDFView()
        view.kwargs = {"pk": 9}

        assert view.get_download_name() == "0001-00000032.pdf"
