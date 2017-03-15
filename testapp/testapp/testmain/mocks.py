from django_afip.models import TaxPayer


def taxpayer():
    return TaxPayer.objects.create(
        name='Test Taxpayer',
        cuit=20329642330,
        is_sandboxed=True,
    )
