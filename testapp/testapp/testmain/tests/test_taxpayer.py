from datetime import datetime

from django.test import TestCase
from factory.django import FileField
from freezegun import freeze_time
from OpenSSL import crypto

from django_afip import factories


class TestTaxPayerKeyManagement(TestCase):

    def test_key_generation(self):
        taxpayer = factories.TaxPayerFactory(key=None)
        taxpayer.generate_key()

        key = taxpayer.key.file.read().decode()
        self.assertEqual(key.splitlines()[0], '-----BEGIN PRIVATE KEY-----')
        self.assertEqual(key.splitlines()[-1], '-----END PRIVATE KEY-----')

        loaded_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
        self.assertIsInstance(loaded_key, crypto.PKey)

    def test_dont_overwrite_keys(self):
        text = "Hello! I'm not really a key :D".encode()
        taxpayer = factories.TaxPayerFactory(key=FileField(data=text))

        taxpayer.generate_key()
        key = taxpayer.key.read()

        self.assertEqual(text, key)

    def test_overwrite_keys_force(self):
        text = "Hello! I'm not really a key :D".encode()
        taxpayer = factories.TaxPayerFactory(key__data=text)

        taxpayer.generate_key(force=True)
        key = taxpayer.key.file.read().decode()

        self.assertNotEqual(text, key)
        self.assertEqual(key.splitlines()[0], '-----BEGIN PRIVATE KEY-----')
        self.assertEqual(key.splitlines()[-1], '-----END PRIVATE KEY-----')

        loaded_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
        self.assertIsInstance(loaded_key, crypto.PKey)

    @freeze_time(datetime.fromtimestamp(1489537017))
    def test_csr_generation(self):
        taxpayer = factories.TaxPayerFactory(key=None)
        taxpayer.generate_key()

        csr_file = taxpayer.generate_csr()
        csr = csr_file.read().decode()

        self.assertEqual(
            csr.splitlines()[0],
            '-----BEGIN CERTIFICATE REQUEST-----'
        )

        self.assertEqual(
            csr.splitlines()[-1],
            '-----END CERTIFICATE REQUEST-----'
        )

        loaded_csr = crypto.load_certificate_request(crypto.FILETYPE_PEM, csr)
        self.assertIsInstance(loaded_csr, crypto.X509Req)

        expected_components = [
            (b'O', b'John Smith'),
            (b'CN', b'djangoafip1489537017'),
            (b'serialNumber', b'CUIT 20329642330'),
        ]

        self.assertEqual(
            expected_components,
            loaded_csr.get_subject().get_components()
        )


class TaxPayerCertificateObjectTestCase(TestCase):
    def test_certificate_object(self):
        taxpayer = factories.TaxPayerFactory()
        cert = taxpayer.certificate_object

        self.assertIsInstance(cert, crypto.X509)

    def test_null_certificate_object(self):
        taxpayer = factories.TaxPayerFactory(certificate=None)
        cert = taxpayer.certificate_object

        self.assertIsNone(cert)


class TaxPayerExpirationTestCase(TestCase):
    def test_expiration_getter(self):
        taxpayer = factories.TaxPayerFactory()
        expiration = taxpayer.get_certificate_expiration()

        self.assertIsInstance(expiration, datetime)

    def test_expiration_signal_update(self):
        taxpayer = factories.TaxPayerFactory(certificate_expiration=None)
        taxpayer.save()
        expiration = taxpayer.certificate_expiration

        self.assertIsInstance(expiration, datetime)
