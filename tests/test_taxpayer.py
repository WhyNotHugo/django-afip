from __future__ import annotations

from datetime import datetime

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.x509.oid import NameOID
from factory.django import FileField
from freezegun import freeze_time
from OpenSSL.crypto import X509

from django_afip import factories


@pytest.mark.django_db
def test_key_generation() -> None:
    taxpayer = factories.TaxPayerFactory.build(key=None)
    taxpayer.generate_key()

    key = taxpayer.key.file.read().decode()
    assert key.splitlines()[0] == "-----BEGIN PRIVATE KEY-----"
    assert key.splitlines()[-1] == "-----END PRIVATE KEY-----"

    loaded_key = load_pem_private_key(key, password=None)
    assert loaded_key is not None


def test_dont_overwrite_keys() -> None:
    text = b"Hello! I'm not really a key :D"
    taxpayer = factories.TaxPayerFactory.build(key=FileField(data=text))

    taxpayer.generate_key()
    key = taxpayer.key.read()

    assert text == key


@pytest.mark.django_db
def test_overwrite_keys_force() -> None:
    text = b"Hello! I'm not really a key :D"
    taxpayer = factories.TaxPayerFactory.build(key__data=text)

    taxpayer.generate_key(force=True)
    key = taxpayer.key.file.read().decode()

    assert text != key
    assert key.splitlines()[0] == "-----BEGIN PRIVATE KEY-----"
    assert key.splitlines()[-1] == "-----END PRIVATE KEY-----"

    loaded_key = load_pem_private_key(key, password=None)
    assert loaded_key is not None


@freeze_time(datetime.fromtimestamp(1489537017))
@pytest.mark.django_db
def test_csr_generation() -> None:
    taxpayer = factories.TaxPayerFactory.build(key=None)
    taxpayer.generate_key()

    csr_file = taxpayer.generate_csr()
    csr = csr_file.read().decode()

    assert csr.splitlines()[0] == "-----BEGIN CERTIFICATE REQUEST-----"

    assert csr.splitlines()[-1] == "-----END CERTIFICATE REQUEST-----"

    loaded_csr = x509.load_pem_x509_csr(csr)
    assert isinstance(loaded_csr, x509.CertificateSigningRequest)

    subject = loaded_csr.subject
    assert (
        subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value
        == "John Smith"
    )
    assert (
        subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        == "djangoafip1489537017"
    )
    assert (
        subject.get_attributes_for_oid(NameOID.SERIAL_NUMBER)[0].value
        == "CUIT 20329642330"
    )


def test_certificate_object() -> None:
    taxpayer = factories.TaxPayerFactory.build()
    cert = taxpayer.certificate_object

    assert isinstance(cert, X509)


def test_null_certificate_object() -> None:
    taxpayer = factories.TaxPayerFactory.build(certificate=None)
    cert = taxpayer.certificate_object

    assert cert is None


def test_expiration_getter() -> None:
    taxpayer = factories.TaxPayerFactory.build(certificate=None)
    expiration = taxpayer.get_certificate_expiration()

    assert expiration is None


def test_expiration_getter_no_cert() -> None:
    taxpayer = factories.TaxPayerFactory.build()
    expiration = taxpayer.get_certificate_expiration()

    assert isinstance(expiration, datetime)


@pytest.mark.django_db
def test_expiration_signal_update() -> None:
    taxpayer = factories.TaxPayerFactory(certificate_expiration=None)
    taxpayer.save()
    expiration = taxpayer.certificate_expiration

    assert isinstance(expiration, datetime)
