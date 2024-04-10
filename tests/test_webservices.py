"""Tests for AFIP-WS related classes."""

from __future__ import annotations

from datetime import date
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core import management
from factory.django import FileField
from pytest_django.asserts import assertQuerySetEqual

from django_afip import exceptions
from django_afip import factories
from django_afip import models


@pytest.mark.live()
@pytest.mark.django_db()
def test_authentication_with_bad_cuit() -> None:
    """Test using the wrong cuit for a key pair."""

    taxpayer = factories.AlternateTaxpayerFactory(cuit=20329642339)
    taxpayer.create_ticket("wsfe")

    with pytest.raises(
        exceptions.AfipException,
        # Note: AFIP apparently edited this message and added a typo:
        match="ValidacionDeToken: No apareci[oó] CUIT en lista de relaciones:",
    ):
        taxpayer.fetch_points_of_sales()


@pytest.mark.live()
@pytest.mark.django_db()
def test_authentication_with_bogus_certificate_exception() -> None:
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


@pytest.mark.live()
@pytest.mark.django_db()
def test_authentication_with_no_active_taxpayer() -> None:
    """Test that no TaxPayers raises an understandable error."""
    with pytest.raises(
        exceptions.AuthenticationError,
        match="There are no taxpayers to generate a ticket.",
    ):
        models.AuthTicket.objects.get_any_active("wsfe")


@pytest.mark.live()
@pytest.mark.django_db()
def test_authentication_with_expired_certificate_exception() -> None:
    """Test that using an expired ceritificate raises as expected."""
    taxpayer = factories.TaxPayerFactory(
        key=FileField(from_path=factories.get_test_file("test_expired.key")),
        certificate=FileField(from_path=factories.get_test_file("test_expired.crt")),
    )

    with pytest.raises(exceptions.CertificateExpired):
        taxpayer.create_ticket("wsfe")


@pytest.mark.live()
@pytest.mark.django_db()
def test_authentication_with_untrusted_certificate_exception() -> None:
    """
    Test that using an untrusted ceritificate raises as expected.
    """
    # Note that we hit production with a sandbox cert here:
    taxpayer = factories.TaxPayerFactory(is_sandboxed=False)

    with pytest.raises(exceptions.UntrustedCertificate):
        taxpayer.create_ticket("wsfe")


@pytest.mark.django_db()
def test_population_command() -> None:
    """Test the afipmetadata command."""
    management.call_command("afipmetadata")

    assert models.ReceiptType.objects.count() > 0
    assert models.ConceptType.objects.count() > 0
    assert models.DocumentType.objects.count() > 0
    assert models.VatType.objects.count() > 0
    assert models.TaxType.objects.count() > 0
    assert models.CurrencyType.objects.count() > 0


@pytest.mark.django_db()
def test_metadata_deserialization() -> None:
    """Test that we deserialize descriptions properly."""
    management.call_command("afipmetadata")

    # This assertion is tied to current data, but it validates that we
    # don't mess up encoding/decoding the value we get.
    # It _WILL_ need updating if the upstream value ever changes.
    fac_c = models.ReceiptType.objects.get(code=11)
    assert fac_c.description == "Factura C"


@pytest.mark.django_db()
@pytest.mark.live()
def test_taxpayer_fetch_points_of_sale(populated_db: None) -> None:
    """Test the ``fetch_points_of_sales`` method."""
    taxpayer = models.TaxPayer.objects.first()

    assert taxpayer is not None
    taxpayer.fetch_points_of_sales()

    points_of_sales = models.PointOfSales.objects.count()
    assert points_of_sales > 0


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validate_empty(populated_db: None) -> None:
    factories.ReceiptFactory()

    # TYPING: django-stubs can't handle methods in querysets
    errs = models.Receipt.objects.none().validate()  # type: ignore[attr-defined]

    assert errs == []
    assert models.ReceiptValidation.objects.count() == 0


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validation_good(populated_db: None) -> None:
    """Test validating valid receipts."""
    r1 = factories.ReceiptWithVatAndTaxFactory()
    r2 = factories.ReceiptWithVatAndTaxFactory()
    r3 = factories.ReceiptWithVatAndTaxFactory()

    # TYPING: django-stubs can't handle methods in querysets
    errs = models.Receipt.objects.all().validate()  # type: ignore[attr-defined]

    assert len(errs) == 0
    assert r1.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert r2.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert r3.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 3


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validation_bad(populated_db: None) -> None:
    """Test validating invalid receipts."""
    factories.ReceiptWithInconsistentVatAndTaxFactory()
    factories.ReceiptWithInconsistentVatAndTaxFactory()
    factories.ReceiptWithInconsistentVatAndTaxFactory()

    errs = models.Receipt.objects.all().validate()  # type: ignore[attr-defined]

    assert len(errs) == 1
    assert errs[0] == (
        "Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: "
        "80, DocNro 203012345 no se encuentra registrado en los padrones "
        "de AFIP y no corresponde a una cuit pais."
    )

    assert models.ReceiptValidation.objects.count() == 0


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validation_mixed(populated_db: None) -> None:
    """
    Test validating a mixture of valid and invalid receipts.

    Receipts are validated by AFIP in-order, so all receipts previous to
    the bad one are validated, and nothing else is even parsed after the
    invalid one.
    """
    r1 = factories.ReceiptWithVatAndTaxFactory()
    factories.ReceiptWithInconsistentVatAndTaxFactory()
    factories.ReceiptWithVatAndTaxFactory()

    errs = models.Receipt.objects.all().validate()  # type: ignore[attr-defined]

    assert len(errs) == 1
    assert errs[0] == (
        "Error 10015: Factura B (CbteDesde igual a CbteHasta), DocTipo: "
        "80, DocNro 203012345 no se encuentra registrado en los padrones "
        "de AFIP y no corresponde a una cuit pais."
    )

    assertQuerySetEqual(
        models.ReceiptValidation.objects.all(),
        [r1.pk],
        lambda rv: rv.receipt_id,
    )


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validation_validated(populated_db: None) -> None:
    """Test validating invalid receipts."""
    factories.ReceiptWithApprovedValidation()

    errs = models.Receipt.objects.all().validate()  # type: ignore[attr-defined]

    assert models.ReceiptValidation.objects.count() == 1
    assert errs == []


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validation_good_service(populated_db: None) -> None:
    """Test validating a receipt for a service (rather than product)."""
    receipt = factories.ReceiptWithVatAndTaxFactory(
        concept__code=2,
        service_start=date.today() - timedelta(days=10),
        service_end=date.today(),
        expiration_date=date.today() + timedelta(days=10),
    )

    errs = models.Receipt.objects.all().validate()  # type: ignore[attr-defined]

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validation_good_without_tax(populated_db: None) -> None:
    """Test validating valid receipts."""
    receipt = factories.ReceiptFactory(
        point_of_sales=models.PointOfSales.objects.first(),
        total_amount=121,
    )
    factories.VatFactory(vat_type__code=5, receipt=receipt)

    errs = models.Receipt.objects.all().validate()  # type: ignore[attr-defined]

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validation_good_without_vat(populated_db: None) -> None:
    """Test validating valid receipts."""
    receipt = factories.ReceiptFactory(
        point_of_sales=models.PointOfSales.objects.first(),
        receipt_type__code=11,
        total_amount=109,
    )
    factories.TaxFactory(tax_type__code=3, receipt=receipt)

    errs = models.Receipt.objects.all().validate()  # type: ignore[attr-defined]

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.xfail(reason="Currently not working -- needs to get looked at.")
@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_validation_with_observations(populated_db: None) -> None:
    receipt = factories.ReceiptFactory(
        document_number=20291144404,
        document_type__code=80,
        point_of_sales=models.PointOfSales.objects.first(),
        receipt_type__code=1,
    )
    factories.VatFactory(vat_type__code=5, receipt=receipt)
    factories.TaxFactory(tax_type__code=3, receipt=receipt)

    errs = models.Receipt.objects.all().validate()  # type: ignore[attr-defined]

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1
    assert models.Observation.objects.count() == 1
    assert receipt.validation.observations.count() == 1


@pytest.mark.django_db()
@pytest.mark.live()
def test_receipt_queryset_credit_note(populated_db: None) -> None:
    """Test validating valid a credit note."""
    # Create an invoice (code=6) and validate it...
    invoice = factories.ReceiptWithVatAndTaxFactory()

    qs = models.Receipt.objects.filter(
        pk=invoice.pk,
    )
    errs = qs.validate()  # type: ignore[attr-defined]
    assert len(errs) == 0
    assert models.ReceiptValidation.objects.count() == 1

    # Now create a credit note (code=8) and validate it...
    credit = factories.ReceiptWithVatAndTaxFactory(receipt_type__code=8)
    credit.related_receipts.set([invoice])
    credit.save()

    qs = models.Receipt.objects.filter(pk=credit.pk)
    errs = qs.validate()  # type: ignore[attr-defined]
    assert len(errs) == 0
    assert models.ReceiptValidation.objects.count() == 2
