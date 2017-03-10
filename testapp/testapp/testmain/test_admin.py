from unittest import mock

from django.contrib import messages
from django.http import HttpRequest
from django.test import TestCase
from django.utils.translation import ugettext as _

from django_afip import exceptions
from django_afip.admin import catch_errors


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
            _('An unknown authentication error has ocurred.'),
            messages.ERROR,
        ))
