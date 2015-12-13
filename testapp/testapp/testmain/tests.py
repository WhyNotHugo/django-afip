from datetime import date
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.test import TestCase, Client

from django_afip import models

# We keep the taxpayer and it's ticket in-memory, since the webservice does not
# allow too frequent requests, and each unit test needs a ticket to work.


class AfipTestCase(TestCase):

    taxpayer = None
    ticket = None

    def setUp(self):
        if not AfipTestCase.taxpayer:
            taxpayer = models.TaxPayer(
                pk=1,
                name='test taxpayer',
                cuit=20329642330,
            )

            basepath = settings.BASE_DIR
            with open(os.path.join(basepath, 'test.key')) as key:
                taxpayer.key.save('test.key', File(key))
            with open(os.path.join(basepath, 'test.crt')) as crt:
                taxpayer.certificate.save('test.crt', File(crt))

            AfipTestCase.taxpayer = taxpayer

        if not AfipTestCase.ticket:
            ticket = models.AuthTicket.objects.get_any_active('wsfe')
            AfipTestCase.ticket = ticket

        AfipTestCase.taxpayer.save()
        AfipTestCase.ticket.save()


class AuthTicketTest(TestCase):

    def test_no_active_taxpayer(self):
        with self.assertRaisesMessage(
            Exception,
            'There are no taxpayers to generate a ticket.',
        ):
            models.AuthTicket.objects.get_any_active('wsfe')


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


class ReceiptBatchTest(AfipTestCase):

    def setUp(self):
        super().setUp()
        models.populate_all()
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

    def _good_receipt(self):
        receipt = models.Receipt(
            concept=models.ConceptType.objects.get(code=1),
            document_type=models.DocumentType.objects.get(code=96),
            document_number="30123456",
            issued_date=date.today(),
            total_amount=121,
            net_untaxed=0,
            net_taxed=100,
            exempt_amount=0,
            currency=models.CurrencyType.objects.get(code='PES'),
            currency_quote=1,

            receipt_type=models.ReceiptType.objects.get(code=6),
            point_of_sales=models.PointOfSales.objects.first(),
        )
        receipt.save()
        models.Vat(
            vat_type=models.VatType.objects.get(code=5),
            base_amount=100,
            amount=21,
            receipt=receipt,
        ).save()

        return receipt

    def _bad_receipt(self):
        receipt = models.Receipt(
            concept=models.ConceptType.objects.get(code=1),
            document_type=models.DocumentType.objects.get(code=80),
            document_number="203012345",
            issued_date=date.today(),
            total_amount=121,
            net_untaxed=0,
            net_taxed=100,
            exempt_amount=0,
            currency=models.CurrencyType.objects.get(code='PES'),
            currency_quote=1,

            receipt_type=models.ReceiptType.objects.get(code=6),
            point_of_sales=models.PointOfSales.objects.first(),
        )
        receipt.save()
        models.Vat(
            vat_type=models.VatType.objects.get(code=5),
            base_amount=100,
            amount=21,
            receipt=receipt,
        ).save()

        return receipt

    def test_creation_empty(self):
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.none(),
        )
        self.assertIsNone(batch)

    def test_creation_exclusion(self):
        """
        Test that batch creation excludes already batched receipts.
        """
        self._good_receipt()
        self._good_receipt()
        self._good_receipt()

        models.ReceiptBatch.objects.create(
            models.Receipt.objects.filter(pk=1),
        )
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.filter(batch_id__isnull=True),
        )

        self.assertEquals(batch.receipts.count(), 2)

    def test_validate_empty(self):
        # Hack to easily create an empty batch:
        self._good_receipt()
        batch = models.ReceiptBatch.objects.create(
            models.Receipt.objects.all(),
        )
        models.Receipt.objects.all().delete()

        errs = batch.validate()
        self.assertIsNone(errs)

    def test_validation_good(self):
        self._good_receipt()
        self._good_receipt()
        self._good_receipt()

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            batch.validation.last().result,
            models.Validation.RESULT_APPROVED,
        )
        self.assertEqual(batch.receipts.count(), 3)

    def test_validation_bad(self):
        self._bad_receipt()
        self._bad_receipt()
        self._bad_receipt()

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs[0],
            'Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: '
            '80, DocNro 203012345 no se encuentra registrado en los padrones '
            'de AFIP y no corresponde a una cuit pais.'
        )
        self.assertEqual(batch.receipts.count(), 0)

    def test_validation_mixed(self):
        self._good_receipt()
        self._bad_receipt()
        self._good_receipt()

        batch = models.ReceiptBatch.objects \
            .create(models.Receipt.objects.all())
        errs = batch.validate()

        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs[0],
            'Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: '
            '80, DocNro 203012345 no se encuentra registrado en los padrones '
            'de AFIP y no corresponde a una cuit pais.'
        )
        self.assertEqual(batch.receipts.count(), 1)
