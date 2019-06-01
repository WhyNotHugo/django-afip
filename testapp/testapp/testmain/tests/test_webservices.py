"""Tests for AFIP-WS related classes."""
import os
from datetime import datetime, timedelta
from unittest import skip
from unittest.mock import patch

from django.conf import settings
from django.core import management
from django.test import tag, TestCase
from django.utils.timezone import now
from factory.django import FileField

from django_afip import exceptions, factories, models
from testapp.testmain.tests.testcases import (
    LiveAfipTestCase,
    PopulatedLiveAfipTestCase,
)


@tag('live')
class AuthTicketTest(TestCase):
    """Test AuthTicket methods."""

    def test_bad_cuit(self):
        """Test using the wrong cuit for a key pair."""

        taxpayer = factories.AlternateTaxpayerFactory(cuit=20329642339)
        taxpayer.create_ticket('wsfe')

        with self.assertRaisesRegex(
            exceptions.AfipException,
            # Note: AFIP apparently edited this message and added a typo:
            'ValidacionDeToken: No apareci[oó] CUIT en lista de relaciones:',
        ):
            models.populate_all()

    def test_bogus_certificate_exception(self):
        """Test that using a junk ceritificates raises as expected."""

        # New TaxPayers will fail to save with an invalid cert, but many
        # systems may have very old TaxPayers, externally created, or other
        # stuff, so this scenario might still be possible.
        with patch(
            'django_afip.models.TaxPayer.get_certificate_expiration',
            spec=True,
            return_value=None,
        ):
            taxpayer = factories.TaxPayerFactory(
                key=FileField(data=b'Blah'),
                certificate=FileField(data=b'Blah'),
            )

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
        with open(
            os.path.join(settings.BASE_DIR, 'test_expired.key'),
        ) as key, open(
            os.path.join(settings.BASE_DIR, 'test_expired.crt'),
        ) as crt:
            taxpayer = factories.TaxPayerFactory(
                key=FileField(from_file=key),
                certificate=FileField(from_file=crt),
            )

        with self.assertRaises(exceptions.CertificateExpired):
            taxpayer.create_ticket('wsfe')

    def test_untrusted_certificate_exception(self):
        """
        Test that using an untrusted ceritificate raises as expected.
        """
        # Note that we hit production with a sandbox cert here:
        taxpayer = factories.TaxPayerFactory(is_sandboxed=False)

        with self.assertRaises(exceptions.UntrustedCertificate):
            taxpayer.create_ticket('wsfe')


class PopulationTest(LiveAfipTestCase):
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

    def test_metadata_deserialization(self):
        """Test that we deserialize descriptions properly."""
        management.call_command('afipmetadata')

        # This asserting is tied to current data, but it validates that we
        # don't mess up encoding/decoding the value we get.
        # It _WILL_ need updating if the upstream value ever changes.
        fac_c = models.ReceiptType.objects.get(code=11)
        self.assertEqual(fac_c.description, 'Factura C')


class TaxPayerTest(LiveAfipTestCase):
    """Test TaxPayer methods."""

    def test_fetch_points_of_sale(self):
        """Test the ``fetch_points_of_sales`` method."""
        taxpayer = models.TaxPayer.objects.first()
        taxpayer.fetch_points_of_sales()

        points_of_sales = models.PointOfSales.objects.count()
        self.assertGreater(points_of_sales, 0)


class ReceiptQuerySetTestCase(PopulatedLiveAfipTestCase):
    """Test ReceiptQuerySet methods."""

    def _good_receipt(self):
        receipt = factories.ReceiptFactory(
            point_of_sales=models.PointOfSales.objects.first(),
        )
        factories.VatFactory(vat_type__code=5, receipt=receipt)
        factories.TaxFactory(tax_type__code=3, receipt=receipt)
        return receipt

    def _bad_receipt(self):
        receipt = factories.ReceiptFactory(
            point_of_sales=models.PointOfSales.objects.first(),
            document_type__code=80,
        )
        factories.VatFactory(vat_type__code=5, receipt=receipt)
        factories.TaxFactory(tax_type__code=3, receipt=receipt)
        return receipt

    def test_validate_empty(self):
        factories.ReceiptFactory()

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
        receipt = factories.ReceiptFactory(
            point_of_sales=models.PointOfSales.objects.first(),
            total_amount=121,
        )
        factories.VatFactory(vat_type__code=5, receipt=receipt)

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            receipt.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 1)

    def test_validation_good_without_vat(self):
        """Test validating valid receipts."""
        receipt = factories.ReceiptFactory(
            point_of_sales=models.PointOfSales.objects.first(),
            receipt_type__code=11,
            total_amount=109,
        )
        factories.TaxFactory(tax_type__code=3, receipt=receipt)

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            receipt.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 1)

    @skip('Currently not working -- needs to get looked at.')
    def test_validation_with_observations(self):
        receipt = factories.ReceiptFactory(
            document_number=20291144404,
            document_type__code=80,
            point_of_sales=models.PointOfSales.objects.first(),
            receipt_type__code=1,
        )
        factories.VatFactory(vat_type__code=5, receipt=receipt)
        factories.TaxFactory(tax_type__code=3, receipt=receipt)

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 0)
        self.assertEqual(
            receipt.validation.result,
            models.ReceiptValidation.RESULT_APPROVED,
        )
        self.assertEqual(models.ReceiptValidation.objects.count(), 1)
        self.assertEqual(models.Observation.objects.count(), 1)
        self.assertEqual(receipt.validation.observations.count(), 1)


# TODO: Test receipts with related_receipts
