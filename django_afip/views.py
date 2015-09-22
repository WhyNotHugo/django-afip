from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from . import models


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
