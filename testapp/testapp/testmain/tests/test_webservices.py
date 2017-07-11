"""Tests for AFIP-WS related classes."""
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.core import management
from django.core.files import File
from django.test import tag, TestCase
from django.utils.timezone import now

from django_afip import exceptions, models
from testapp.testmain import fixtures, mocks


@tag('live')
class AfipTestCase(TestCase):
    """
    Base class for AFIP-WS related tests.

    Since AFIP rate-limits how often authentication tokens can be fetched, we
    need to keep one between tests.
    This class is a simple hack to keep that ticket in-memory and saves it into
    the DB every time a new class is ``setUp``.
    """

    taxpayer = None
    ticket = None

    def setUp(self):
        """Save a TaxPayer and Ticket into the database."""
        if not AfipTestCase.taxpayer:
            taxpayer = models.TaxPayer(
                pk=1,
                name='test taxpayer',
                cuit=20329642330,
                is_sandboxed=True,
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


@tag('live')
class AuthTicketTest(TestCase):
    """Test AuthTicket methods."""

    def test_bad_cuit(self):
        """Test using the wrong cuit for a key pair."""

        taxpayer = models.TaxPayer(
            pk=1,
            name='test taxpayer',
            # This is the wrong CUIT for our keypair:
            cuit=20329642339,
            is_sandboxed=True,
        )
        basepath = settings.BASE_DIR
        with open(os.path.join(basepath, 'test.key')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test.crt')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))
        taxpayer.save()

        taxpayer.create_ticket('wsfe')

        with self.assertRaisesRegex(
            exceptions.AfipException,
            # Note: AFIP apparently edited this message and added a typo:
            'ValidacionDeToken: No apareci[oó] CUIT en lista de relaciones:',
        ):
            models.populate_all()

    def test_bogus_certificate_exception(self):
        """Test that using a junk ceritificates raises as expected."""
        taxpayer = models.TaxPayer(
            pk=1,
            name='test taxpayer',
            cuit=20329642330,
            is_sandboxed=True,
        )
        # Note that we swap key and crt so that it's bogus input:
        basepath = settings.BASE_DIR
        with open(os.path.join(basepath, 'test.crt')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test.key')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))
        taxpayer.save()

        with self.assertRaises(exceptions.CorruptCertificate) as e:
            taxpayer.create_ticket('wsfe')

        self.assertNotIsInstance(e, exceptions.AfipException)

    def test_no_active_taxpayer(self):
        """Test that no TaxPayers raises an understandable error."""
        with self.assertRaisesMessage(
            exceptions.AuthenticationError,
            'There are no taxpayers to generate a ticket.',
        ):
            models.AuthTicket.objects.get_any_active('wsfe')

    def test_expired_certificate_exception(self):
        """Test that using an expired ceritificate raises as expected."""
        taxpayer = models.TaxPayer(
            pk=1,
            name='test taxpayer',
            cuit=20329642330,
            is_sandboxed=True,
        )
        basepath = settings.BASE_DIR
        with open(os.path.join(basepath, 'test_expired.key')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test_expired.crt')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))
        taxpayer.save()

        with self.assertRaises(exceptions.CertificateExpired):
            taxpayer.create_ticket('wsfe')

    def test_untrusted_certificate_exception(self):
        """
        Test that using an untrusted ceritificate raises as expected.
        """
        taxpayer = models.TaxPayer(
            pk=1,
            name='test taxpayer',
            cuit=20329642330,
            # Note that we hit production with a sandbox cert here:
            is_sandboxed=False,
        )
        basepath = settings.BASE_DIR
        with open(os.path.join(basepath, 'test.key')) as key:
            taxpayer.key.save('test.key', File(key))
        with open(os.path.join(basepath, 'test.crt')) as crt:
            taxpayer.certificate.save('test.crt', File(crt))
        taxpayer.save()

        with self.assertRaises(exceptions.UntrustedCertificate):
            taxpayer.create_ticket('wsfe')


class PopulationTest(AfipTestCase):
    """
    Tests models population view.

    As a side effect, also test valid ticket generation.
    """

    def test_population_command(self):
        """Test the afipmetadata command."""
        management.call_command('afipmetadata')

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
    """Test TaxPayer methods."""

    def test_fetch_points_of_sale(self):
        """Test the ``fetch_points_of_sales`` method."""
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

        points_of_sales = models.PointOfSales.objects.count()
        self.assertGreater(points_of_sales, 0)


class PopulatedAfipTestCase(AfipTestCase):
    def setUp(self):
        """Populate AFIP metadata and create a TaxPayer and PointOfSales."""
        super().setUp()
        models.populate_all()
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()


class ReceiptQuerySetTestCase(PopulatedAfipTestCase):
    """Test ReceiptQuerySet methods."""

    def _good_receipt(self):
        return mocks.receipt()

    def _bad_receipt(self):
        return mocks.receipt(80)

    def test_validate_empty(self):
        fixtures.ReceiptFactory()

        errs = models.Receipt.objects.none().validate()

        self.assertEqual(errs, [])
        self.assertEqual(models.ReceiptValidation.objects.count(), 0)

    def test_validation_good(self):
        """Test validating valid receipts."""
        r1 = self._good_receipt()
        r2 = self._good_receipt()
        r3 = self._good_receipt()

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            r1.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(
            r2.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(
            r3.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 3)

    def test_validation_bad(self):
        """Test validating invalid receipts."""
        self._bad_receipt()
        self._bad_receipt()
        self._bad_receipt()

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs[0],
            'Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: '
            '80, DocNro 203012345 no se encuentra registrado en los padrones '
            'de AFIP y no corresponde a una cuit pais.'
        )
        self.assertQuerysetEqual(models.ReceiptValidation.objects.all(), [])

    def test_validation_mixed(self):
        """
        Test validating a mixture of valid and invalid receipts.

        Receipts are validated by AFIP in-order, so all receipts previous to
        the bad one are validated, and nothing else is even parsed after the
        invalid one.
        """
        r1 = self._good_receipt()
        self._bad_receipt()
        self._good_receipt()

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs[0],
            'Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: '
            '80, DocNro 203012345 no se encuentra registrado en los padrones '
            'de AFIP y no corresponde a una cuit pais.'
        )
        self.assertQuerysetEqual(
            models.ReceiptValidation.objects.all(),
            [r1.pk],
            lambda rv: rv.receipt_id,
        )

    def test_validation_validated(self):
        """Test validating invalid receipts."""
        receipt = self._good_receipt()
        models.ReceiptValidation.objects.create(
            result=models.ReceiptValidation.RESULT_APPROVED,
            cae='123',
            cae_expiration=now(),
            receipt=receipt,
            processed_date=now(),
        )

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(models.ReceiptValidation.objects.count(), 1)
        self.assertEqual(errs, [])

    def test_validation_good_service(self):
        """Test validating a receipt for a service (rather than product)."""
        receipt = self._good_receipt()
        receipt.concept_id = 2
        receipt.service_start = datetime.now() - timedelta(days=10)
        receipt.service_end = datetime.now()
        receipt.expiration_date = datetime.now() + timedelta(days=10)
        receipt.save()

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            receipt.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 1)

    def test_validation_good_without_tax(self):
        """Test validating valid receipts."""
        receipt = mocks.receipt(with_tax=False)

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            receipt.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 1)

    def test_validation_good_without_vat(self):
        """Test validating valid receipts."""
        receipt = mocks.receipt(with_vat=False, receipt_type=11)

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            receipt.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 1)


# TODO: Test receipts with related_receipts
