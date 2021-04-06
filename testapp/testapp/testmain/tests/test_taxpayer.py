from datetime import datetime

import pytest
from factory.django import FileField
from freezegun import freeze_time
from OpenSSL import crypto

from django_afip import factories


@pytest.mark.django_db
def test_key_generation():
    taxpayer = factories.TaxPayerFactory.build(key=None)
    taxpayer.generate_key()

    key = taxpayer.key.file.read().decode()
    assert key.splitlines()[0] == "-----BEGIN PRIVATE KEY-----"
    assert key.splitlines()[-1] == "-----END PRIVATE KEY-----"

    loaded_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
    assert isinstance(loaded_key, crypto.PKey)


def test_dont_overwrite_keys():
    text = b"Hello! I'm not really a key :D"
    taxpayer = factories.TaxPayerFactory.build(key=FileField(data=text))

    taxpayer.generate_key()
    key = taxpayer.key.read()

    assert text == key


@pytest.mark.django_db
def test_overwrite_keys_force():
    text = b"Hello! I'm not really a key :D"
    taxpayer = factories.TaxPayerFactory.build(key__data=text)

    taxpayer.generate_key(force=True)
    key = taxpayer.key.file.read().decode()

    assert text != key
    assert key.splitlines()[0] == "-----BEGIN PRIVATE KEY-----"
    assert key.splitlines()[-1] == "-----END PRIVATE KEY-----"

    loaded_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
    assert isinstance(loaded_key, crypto.PKey)


@freeze_time(datetime.fromtimestamp(1489537017))
@pytest.mark.django_db
def test_csr_generation():
    taxpayer = factories.TaxPayerFactory.build(key=None)
    taxpayer.generate_key()

    csr_file = taxpayer.generate_csr()
    csr = csr_file.read().decode()

    assert csr.splitlines()[0] == "-----BEGIN CERTIFICATE REQUEST-----"

    assert csr.splitlines()[-1] == "-----END CERTIFICATE REQUEST-----"

    loaded_csr = crypto.load_certificate_request(crypto.FILETYPE_PEM, csr)
    assert isinstance(loaded_csr, crypto.X509Req)

    expected_components = [
        (b"O", b"John Smith"),
        (b"CN", b"djangoafip1489537017"),
        (b"serialNumber", b"CUIT 20329642330"),
    ]

    assert expected_components == loaded_csr.get_subject().get_components()


def test_certificate_object():
    taxpayer = factories.TaxPayerFactory.build()
    cert = taxpayer.certificate_object

    assert isinstance(cert, crypto.X509)


def test_null_certificate_object():
    taxpayer = factories.TaxPayerFactory.build(certificate=None)
    cert = taxpayer.certificate_object

    assert cert is None


def test_expiration_getter():
    taxpayer = factories.TaxPayerFactory.build()
    expiration = taxpayer.get_certificate_expiration()

    assert isinstance(expiration, datetime)


@pytest.mark.django_db
def test_expiration_signal_update():
    taxpayer = factories.TaxPayerFactory(certificate_expiration=None)
    taxpayer.save()
    expiration = taxpayer.certificate_expiration

    assert isinstance(expiration, datetime)
