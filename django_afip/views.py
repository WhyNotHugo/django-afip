from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.views.generic import View

from . import models
from .pdf import generate_receipt_pdf


@login_required
def populate_models(request):
    """
    Locally populates all models for AFIP-defined types.
    """
    if not request.user.is_superuser:
        return HttpResponse(
            'Only superusers can access this endpoint',
            status=403,
        )

    models.populate_all()

    return HttpResponse('Success')


class ReceiptHTMLView(View):
    template_name = 'django_afip/invoice.html'

    def get(self, request, pk):
        return HttpResponse(
            generate_receipt_pdf(pk, request, True),
        )


class ReceiptPDFView(View):

    def get(self, request, pk):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename=' + \
            _('receipt %s.pdf').format(pk)

        generate_receipt_pdf(pk, response)
        return response
