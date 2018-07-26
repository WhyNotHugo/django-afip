import base64

from django.utils.functional import cached_property
from django_renderpdf.views import PDFView

from django_afip import models, pdf


class ReceiptPDFView(PDFView):
    @cached_property
    def receipt(self):
        return models.Receipt.objects.select_related(
            'receipt_type',
            'point_of_sales',
        ).get(
            pk=self.kwargs['pk'],
        )

    def get_download_name(self):
        return '{}.pdf'.format(self.receipt.formatted_number)

    def get_template_name(self):
        return 'receipts/code_{}.html'.format(self.receipt.receipt_type.code)

    @staticmethod
    def get_context_for_pk(pk, *args, **kwargs):
        context = {}

        receipt_pdf = models.ReceiptPDF.objects.select_related(
            'receipt',
            'receipt__receipt_type',
            'receipt__document_type',
            'receipt__validation',
            'receipt__point_of_sales',
            'receipt__point_of_sales__owner',
        ).prefetch_related(
            'receipt__entries',
        ).get(
            receipt__pk=pk,
        )

        # Prefetch required data in a single query:
        receipt_pdf.receipt = models.Receipt.objects.select_related(
            'receipt_type',
            'document_type',
            'validation',
            'point_of_sales',
            'point_of_sales__owner',
        ).prefetch_related(
            'entries',
        ).get(
            pk=receipt_pdf.receipt_id,
        )
        taxpayer = receipt_pdf.receipt.point_of_sales.owner
        extras = models.TaxPayerExtras.objects.filter(
            taxpayer=taxpayer,
        ).first()

        generator = pdf.ReceiptBarcodeGenerator(receipt_pdf.receipt)
        barcode = base64.b64encode(generator.generate_barcode())

        context['pdf'] = receipt_pdf
        context['taxpayer'] = taxpayer
        context['extras'] = extras
        context['barcode'] = barcode.decode()

        return context

    def get_context_data(self, *args, pk=None, **kwargs):
        context = super().get_context_data(*args, pk=pk, **kwargs)
        context.update(self.get_context_for_pk(pk, *args, **kwargs))
        return context


class ReceiptPDFDownloadView(ReceiptPDFView):
    prompt_download = True
