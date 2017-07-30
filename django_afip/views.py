from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.views.generic import View

from .pdf import generate_receipt_pdf


class ReceiptHTMLView(View):
    """Renders a receipt as HTML."""
    def get(self, request, pk):
        return HttpResponse(
            generate_receipt_pdf(pk, request, True),
        )


class ReceiptPDFView(View):
    """Renders a receipt as a PDF, prompting to download it."""

    def get(self, request, pk):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=' + \
            _('receipt %s.pdf' % pk)

        generate_receipt_pdf(pk, response)
        return response


class ReceiptPDFDisplayView(View):
    """
    Renders a receipt as a PDF.

    Browsers should render the file, rather than prompt to download it.
    """
    def get(self, request, pk):
        response = HttpResponse(content_type='application/pdf')
        generate_receipt_pdf(pk, response)
        return response
