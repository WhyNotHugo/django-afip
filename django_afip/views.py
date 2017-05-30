from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.views.generic import View

from .pdf import generate_receipt_pdf


class ReceiptHTMLView(View):

    def get(self, request, pk):
        return HttpResponse(
            generate_receipt_pdf(pk, request, True),
        )


class ReceiptPDFView(View):

    def get(self, request, pk):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=' + \
            _('receipt %s.pdf' % pk)

        generate_receipt_pdf(pk, response)
        return response
