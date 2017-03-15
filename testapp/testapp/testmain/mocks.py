from tempfile import NamedTemporaryFile

from django.contrib.auth.models import User
from django.core.files.base import File
from django_afip.models import TaxPayer


def taxpayer(key=None):
    taxpayer = TaxPayer.objects.create(
        name='Test Taxpayer',
        cuit=20329642330,
        is_sandboxed=True,
    )

    if key:
        with NamedTemporaryFile(suffix='.key') as file_:
            file_.write(key)
            taxpayer.key = File(file_, name='test.key')
            taxpayer.save()

    return taxpayer


def superuser():
    return User.objects.create_superuser('test', 'test@example.com', '123')
