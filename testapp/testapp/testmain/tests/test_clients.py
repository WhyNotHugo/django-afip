from unittest.mock import patch

from django.test import TestCase

from django_afip.clients import get_client


class TestGetService(TestCase):
    def test_services_are_cached(self):
        service1 = get_client('wsfe', False)
        with patch.dict('django_afip.clients.WSDLS', values={}, clear=True):
            service2 = get_client('wsfe', False)

        self.assertEqual(service1, service2)

    def test_inexisting_service(self):
        with self.assertRaisesMessage(
            ValueError,
            'Unknown service name, nonexistant'
        ):
            get_client('nonexistant', False)
