import base64

from django.utils.functional import cached_property
from django_renderpdf.views import PDFView

from django_afip import models
from django_afip import pdf


TEMPLATE_NAMES = [
    "receipts/{taxpayer}/pos_{point_of_sales}/code_{code}.html",
    "receipts/{taxpayer}/code_{code}.html",
    "receipts/code_{code}.html",
    "receipts/{code}.html",
]


class ReceiptPDFView(PDFView):
    @cached_property
    def receipt(self):
        return models.Receipt.objects.select_related(
            "receipt_type",
            "point_of_sales",
        ).get(
            pk=self.kwargs["pk"],
        )

    def get_download_name(self):
        return "{}.pdf".format(self.receipt.formatted_number)

    def get_template_names(self, receipt: models.Receipt = None):
        f"""Return the templates use to render the Receipt PDF.

        Template discovery tries to find any of the below receipts::

            {TEMPLATE_NAMES}

        For example, to override the "Factura C" template for point of sales 0002 for
        Taxpayer 20-32964233-0, use::

            receipts/20329642330/pos_2/code_6.html
        """
        receipt = receipt or self.receipt
        assert receipt is not None

        return [
            template.format(
                taxpayer=receipt.point_of_sales.owner.cuit,
                point_of_sales=receipt.point_of_sales.number,
                code=receipt.receipt_type.code,
            )
            for template in TEMPLATE_NAMES
        ]

    @staticmethod
    def get_context_for_pk(pk, *args, **kwargs):
        context = {}

        receipt_pdf = (
            models.ReceiptPDF.objects.select_related(
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
            .get(
                receipt__pk=pk,
            )
        )

        # Prefetch required data in a single query:
        receipt_pdf.receipt = (
            models.Receipt.objects.select_related(
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
        extras = models.TaxPayerExtras.objects.filter(
            taxpayer=taxpayer,
        ).first()

        generator = pdf.ReceiptBarcodeGenerator(receipt_pdf.receipt)
        barcode = base64.b64encode(generator.generate_barcode())

        context["pdf"] = receipt_pdf
        context["taxpayer"] = taxpayer
        context["extras"] = extras
        context["barcode"] = barcode.decode()

        return context

    def get_context_data(self, *args, pk=None, **kwargs):
        context = super().get_context_data(*args, pk=pk, **kwargs)
        context.update(self.get_context_for_pk(pk, *args, **kwargs))
        return context


class ReceiptPDFDownloadView(ReceiptPDFView):
    prompt_download = True
