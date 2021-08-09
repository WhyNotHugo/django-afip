"""Tests for AFIP-WS related classes."""
from datetime import datetime
from datetime import timedelta
from unittest import skip
from unittest.mock import patch

import pytest
from django.core import management
from django.utils.timezone import now
from factory.django import FileField

from django_afip import exceptions
from django_afip import factories
from django_afip import models
from testapp.testmain.tests.testcases import LiveAfipTestCase
from testapp.testmain.tests.testcases import PopulatedLiveAfipTestCase


@pytest.mark.live
@pytest.mark.django_db
def test_bad_cuit():
    """Test using the wrong cuit for a key pair."""

    taxpayer = factories.AlternateTaxpayerFactory(cuit=20329642339)
    taxpayer.create_ticket("wsfe")

    with pytest.raises(
        exceptions.AfipException,
        # Note: AFIP apparently edited this message and added a typo:
        match="ValidacionDeToken: No apareci[oó] CUIT en lista de relaciones:",
    ):
        taxpayer.fetch_points_of_sales()


@pytest.mark.live
@pytest.mark.django_db
def test_bogus_certificate_exception():
    """Test that using a junk ceritificates raises as expected."""

    # New TaxPayers will fail to save with an invalid cert, but many
    # systems may have very old TaxPayers, externally created, or other
    # stuff, so this scenario might still be possible.
    with patch(
        "django_afip.models.TaxPayer.get_certificate_expiration",
        spec=True,
        return_value=None,
    ):
        taxpayer = factories.TaxPayerFactory(
            key=FileField(data=b"Blah"),
            certificate=FileField(data=b"Blah"),
        )

    with pytest.raises(exceptions.CorruptCertificate) as e:
        taxpayer.create_ticket("wsfe")

    assert not isinstance(e, exceptions.AfipException)


@pytest.mark.live
@pytest.mark.django_db
def test_no_active_taxpayer():
    """Test that no TaxPayers raises an understandable error."""
    with pytest.raises(
        exceptions.AuthenticationError,
        match="There are no taxpayers to generate a ticket.",
    ):
        models.AuthTicket.objects.get_any_active("wsfe")


@pytest.mark.live
@pytest.mark.django_db
def test_expired_certificate_exception():
    """Test that using an expired ceritificate raises as expected."""
    taxpayer = factories.TaxPayerFactory(
        key=FileField(from_path=factories.get_test_file("test_expired.key")),
        certificate=FileField(from_path=factories.get_test_file("test_expired.crt")),
    )

    with pytest.raises(exceptions.CertificateExpired):
        taxpayer.create_ticket("wsfe")


@pytest.mark.live
@pytest.mark.django_db
def test_untrusted_certificate_exception():
    """
    Test that using an untrusted ceritificate raises as expected.
    """
    # Note that we hit production with a sandbox cert here:
    taxpayer = factories.TaxPayerFactory(is_sandboxed=False)

    with pytest.raises(exceptions.UntrustedCertificate):
        taxpayer.create_ticket("wsfe")


@pytest.mark.django_db
def test_population_command():
    """Test the afipmetadata command."""
    management.call_command("afipmetadata")

    assert models.ReceiptType.objects.count() > 0
    assert models.ConceptType.objects.count() > 0
    assert models.DocumentType.objects.count() > 0
    assert models.VatType.objects.count() > 0
    assert models.TaxType.objects.count() > 0
    assert models.CurrencyType.objects.count() > 0


@pytest.mark.django_db
def test_metadata_deserialization():
    """Test that we deserialize descriptions properly."""
    management.call_command("afipmetadata")

    # This assertion is tied to current data, but it validates that we
    # don't mess up encoding/decoding the value we get.
    # It _WILL_ need updating if the upstream value ever changes.
    fac_c = models.ReceiptType.objects.get(code=11)
    assert fac_c.description == "Factura C"


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

    def test_validate_empty(self):
        factories.ReceiptFactory()

        errs = models.Receipt.objects.none().validate()

        self.assertEqual(errs, [])
        self.assertEqual(models.ReceiptValidation.objects.count(), 0)

    def test_validation_good(self):
        """Test validating valid receipts."""
        r1 = factories.ReceiptWithVatAndTaxFactory()
        r2 = factories.ReceiptWithVatAndTaxFactory()
        r3 = factories.ReceiptWithVatAndTaxFactory()

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
        factories.ReceiptWithInconsistentVatAndTaxFactory()
        factories.ReceiptWithInconsistentVatAndTaxFactory()
        factories.ReceiptWithInconsistentVatAndTaxFactory()

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs[0],
            "Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: "
            "80, DocNro 203012345 no se encuentra registrado en los padrones "
            "de AFIP y no corresponde a una cuit pais.",
        )
        self.assertQuerysetEqual(models.ReceiptValidation.objects.all(), [])

    def test_validation_mixed(self):
        """
        Test validating a mixture of valid and invalid receipts.

        Receipts are validated by AFIP in-order, so all receipts previous to
        the bad one are validated, and nothing else is even parsed after the
        invalid one.
        """
        r1 = factories.ReceiptWithVatAndTaxFactory()
        factories.ReceiptWithInconsistentVatAndTaxFactory()
        factories.ReceiptWithVatAndTaxFactory()

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(len(errs), 1)
        self.assertEqual(
            errs[0],
            "Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: "
            "80, DocNro 203012345 no se encuentra registrado en los padrones "
            "de AFIP y no corresponde a una cuit pais.",
        )
        self.assertQuerysetEqual(
            models.ReceiptValidation.objects.all(),
            [r1.pk],
            lambda rv: rv.receipt_id,
        )

    def test_validation_validated(self):
        """Test validating invalid receipts."""
        receipt = factories.ReceiptWithVatAndTaxFactory()
        models.ReceiptValidation.objects.create(
            result=models.ReceiptValidation.RESULT_APPROVED,
            cae="123",
            cae_expiration=now(),
            receipt=receipt,
            processed_date=now(),
        )

        errs = models.Receipt.objects.all().validate()

        self.assertEqual(models.ReceiptValidation.objects.count(), 1)
        self.assertEqual(errs, [])

    def test_validation_good_service(self):
        """Test validating a receipt for a service (rather than product)."""
        receipt = factories.ReceiptWithVatAndTaxFactory()
        receipt.concept = factories.ConceptTypeFactory(code=2)
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

    @skip("Currently not working -- needs to get looked at.")
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

    def test_credit_note(self):
        """Test validating valid a credit note."""
        # Create an invoice (code=6) and validate it...
        invoice = factories.ReceiptWithVatAndTaxFactory()

        errs = models.Receipt.objects.filter(pk=invoice.pk).validate()
        assert len(errs) == 0
        assert models.ReceiptValidation.objects.count() == 1

        # Now create a credit note (code=8) and validate it...
        credit = factories.ReceiptWithVatAndTaxFactory()
        credit.receipt_type = factories.ReceiptTypeFactory(code=8)
        credit.related_receipts.set([invoice])
        credit.save()

        errs = models.Receipt.objects.filter(pk=credit.pk).validate()
        assert len(errs) == 0
        assert models.ReceiptValidation.objects.count() == 2
