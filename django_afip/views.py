from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from .models import ReceiptType, ConceptType, DocumentType, VatType, TaxType, \
    CurrencyType


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

    ReceiptType.objects.populate()
    ConceptType.objects.populate()
    DocumentType.objects.populate()
    VatType.objects.populate()
    TaxType.objects.populate()
    CurrencyType.objects.populate()

    return HttpResponse('Success')
