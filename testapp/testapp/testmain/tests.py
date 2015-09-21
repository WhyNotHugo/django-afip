import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.test import TestCase, Client

from django_afip import models


class AfipTestCase(TestCase):

    def setUp(self):
        taxpayer = models.TaxPayer(
            name='test taxpayer',
            cuit=20329642330,
        )
        basepath = settings.BASE_DIR

        with open(os.path.join(basepath, 'test.key')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test.crt')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))

        taxpayer.save()


class PopulationTest(AfipTestCase):
    """
    Tests models population view.

    As a side effect, also test valid ticket generation.
    """

    def setUp(self):
        super().setUp()
        User.objects._create_user(
            username='normal_user',
            email='normal_user@example.com',
            password='123',
            is_staff=False,
            is_superuser=False,
        )
        User.objects._create_user(
            username='staff_user',
            email='staff_user@example.com',
            password='123',
            is_staff=True,
            is_superuser=False,
        )
        User.objects._create_user(
            username='superuser',
            email='superuser@email.com',
            password='123',
            is_staff=True,
            is_superuser=True,
        )

    def test_normal_user(self):
        c = Client()
        c.login(username='normal_user', password='123')
        r = c.get('/__afip__/populate_models')
        self.assertEqual(r.status_code, 403)

    def test_staff_user(self):
        c = Client()
        c.login(username='staff_user', password='123')
        r = c.get('/__afip__/populate_models')
        self.assertEqual(r.status_code, 403)

    def test_superuser(self):
        c = Client()
        c.login(username='superuser', password='123')
        r = c.get('/__afip__/populate_models')
        self.assertEqual(r.status_code, 200)

        receipts = models.ReceiptType.objects.count()
        concepts = models.ConceptType.objects.count()
        documents = models.DocumentType.objects.count()
        vat = models.VatType.objects.count()
        tax = models.TaxType.objects.count()
        currencies = models.CurrencyType.objects.count()

        self.assertGreater(receipts, 0)
        self.assertGreater(concepts, 0)
        self.assertGreater(documents, 0)
        self.assertGreater(vat, 0)
        self.assertGreater(tax, 0)
        self.assertGreater(currencies, 0)


class TaxPayerTest(AfipTestCase):

    def test_fetch_points_of_sale(self):
        """
        Test the ``fetch_points_of_sales`` method.
        """
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

        points_of_sales = models.PointOfSales.objects.count()
        self.assertGreater(points_of_sales, 0)
