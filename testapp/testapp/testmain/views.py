from django_afip.views import ReceiptPDFView


class ReceiptPDFDownloadView(ReceiptPDFView):
    prompt_download = True
