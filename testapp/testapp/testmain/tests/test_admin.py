from unittest import mock

from django.contrib import messages
from django.http import HttpRequest
from django.test import Client, TestCase
from django.utils.translation import ugettext as _

from django_afip import exceptions
from django_afip.admin import catch_errors
from testapp.testmain import mocks


class TestCatchErrors(TestCase):

    def _get_test_instance(self, exception_type):

        class TestClass(mock.MagicMock):
            @catch_errors
            def action(self, request):
                raise exception_type

        return TestClass()

    def test_certificate_expired(self):
        obj = self._get_test_instance(exceptions.CertificateExpired)

        request = HttpRequest()
        obj.action(request)

        self.assertEqual(obj.message_user.call_count, 1)
        self.assertEqual(obj.message_user.call_args, mock.call(
            request,
            _('The AFIP Taxpayer certificate has expired.'),
            messages.ERROR,
        ))

    def test_certificate_untrusted_cert(self):
        obj = self._get_test_instance(exceptions.UntrustedCertificate)

        request = HttpRequest()
        obj.action(request)

        self.assertEqual(obj.message_user.call_count, 1)
        self.assertEqual(obj.message_user.call_args, mock.call(
            request,
            _('The AFIP Taxpayer certificate is untrusted.'),
            messages.ERROR,
        ))

    def test_certificate_auth_error(self):
        obj = self._get_test_instance(exceptions.AuthenticationError)

        request = HttpRequest()
        obj.action(request)

        self.assertEqual(obj.message_user.call_count, 1)
        self.assertEqual(obj.message_user.call_args, mock.call(
            request,
            _('An unknown authentication error has ocurred: '),
            messages.ERROR,
        ))


class TestTaxPayerAdminKeyGeneration(TestCase):

    def setUp(self):
        self.user = mocks.superuser()

    def test_without_key(self):
        taxpayer = mocks.taxpayer()
        client = Client()
        client.force_login(self.user)

        response = client.post('/admin/afip/taxpayer/', data=dict(
            _selected_action=[taxpayer.id],
            action='generate_key',
        ), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Key generated successfully.')

        taxpayer.refresh_from_db()
        self.assertIn(
            '-----BEGIN PRIVATE KEY-----',
            taxpayer.key.file.read().decode(),
        )

    def test_with_key(self):
        taxpayer = mocks.taxpayer(key='Blah'.encode())
        client = Client()
        client.force_login(self.user)

        response = client.post('/admin/afip/taxpayer/', data=dict(
            _selected_action=[taxpayer.id],
            action='generate_key',
        ), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'No keys generated; Taxpayers already had keys.',
        )

        taxpayer.refresh_from_db()
        self.assertEqual('Blah', taxpayer.key.file.read().decode())


class TestTaxPayerAdminRequestGeneration(TestCase):

    def setUp(self):
        self.user = mocks.superuser()

    def test_with_csr(self):
        taxpayer = mocks.taxpayer()
        taxpayer.generate_key()
        client = Client()
        client.force_login(self.user)

        response = client.post('/admin/afip/taxpayer/', data=dict(
            _selected_action=[taxpayer.id],
            action='generate_csr',
        ), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'Content-Type: application/pkcs10',
            response.serialize_headers().splitlines()
        )
        self.assertContains(
            response,
            '-----BEGIN CERTIFICATE REQUEST-----',
        )

    def test_without_key(self):
        taxpayer = mocks.taxpayer()
        taxpayer.generate_key()
        client = Client()
        client.force_login(self.user)

        response = client.post('/admin/afip/taxpayer/', data=dict(
            _selected_action=[taxpayer.id],
            action='generate_csr',
        ), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            b'Content-Type: application/pkcs10',
            response.serialize_headers().splitlines()
        )
        self.assertContains(
            response,
            '-----BEGIN CERTIFICATE REQUEST-----',
        )

    def test_multiple_taxpayers(self):
        taxpayer1 = mocks.taxpayer(key='Blah'.encode())
        taxpayer2 = mocks.taxpayer(key='Blah'.encode())
        client = Client()
        client.force_login(self.user)

        response = client.post('/admin/afip/taxpayer/', data=dict(
            _selected_action=[taxpayer1.id, taxpayer2.id],
            action='generate_csr',
        ), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'Can only generate CSR for one taxpayer at a time',
        )
