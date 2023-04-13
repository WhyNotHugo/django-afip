from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch

import pytest
from pytest_django.asserts import assertQuerysetEqual

from django_afip import exceptions
from django_afip import factories
from django_afip import models
from django_afip.factories import ReceiptFactory
from django_afip.factories import ReceiptFCEAWithVatAndTaxFactory
from django_afip.factories import ReceiptFCEAWithVatTaxAndOptionalsFactory
from django_afip.factories import ReceiptValidationFactory
from django_afip.factories import ReceiptWithApprovedValidation
from django_afip.factories import ReceiptWithInconsistentVatAndTaxFactory
from django_afip.factories import ReceiptWithVatAndTaxFactory


def test_default_receipt_queryset():
    assert isinstance(models.Receipt.objects.all(), models.ReceiptQuerySet)


@pytest.mark.django_db()
def test_validate():
    receipt = ReceiptFactory()
    queryset = models.Receipt.objects.filter(pk=receipt.pk)
    ticket = MagicMock()

    with patch(
        "django_afip.models.ReceiptQuerySet._assign_numbers",
        spec=True,
    ) as mocked_assign_numbers, patch(
        "django_afip.models.ReceiptQuerySet._validate",
        spec=True,
    ) as mocked__validate:
        queryset.validate(ticket)

    assert mocked_assign_numbers.call_count == 1
    assert mocked__validate.call_count == 1
    assert mocked__validate.call_args == call(ticket)


# TODO: Also another tests that checks that we only pass filtered-out receipts.


def test_default_receipt_manager():
    assert isinstance(models.Receipt.objects, models.ReceiptManager)


@pytest.mark.django_db()
def test_validate_receipt():
    receipt = ReceiptFactory()
    ticket = MagicMock()
    ticket._called = False

    def fake_validate(qs, ticket=None):
        assertQuerysetEqual(qs, [receipt.pk], lambda r: r.pk)
        ticket._called = True

    with patch(
        "django_afip.models.ReceiptQuerySet.validate",
        fake_validate,
    ):
        receipt.validate(ticket)

    assert ticket._called is True


@pytest.mark.django_db()
@pytest.mark.live()
def test_validate_invoice(populated_db):
    """Test validating valid receipts."""

    receipt = ReceiptWithVatAndTaxFactory()
    errs = receipt.validate()

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.django_db()
@pytest.mark.live()
def test_validate_fcea_invoice(populated_db):
    """Test validating valid receipts."""

    receipt = ReceiptFCEAWithVatTaxAndOptionalsFactory()
    errs = receipt.validate()

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.django_db()
@pytest.mark.live()
def test_fail_validate_fcea_invoice(populated_db):
    """Test case to ensure that an invalid FCEA invoice fails."""

    receipt = ReceiptFCEAWithVatAndTaxFactory()
    errs = receipt.validate()

    assert len(errs) == 1
    assert models.ReceiptValidation.objects.count() == 0


@pytest.mark.django_db()
@pytest.mark.live()
def test_validate_credit_note(populated_db):
    """Test validating valid receipts."""

    # Create a receipt (this credit note relates to it):
    receipt = ReceiptWithVatAndTaxFactory()
    errs = receipt.validate()
    assert len(errs) == 0

    # Create a credit note for the above receipt:
    credit_note = ReceiptWithVatAndTaxFactory(receipt_type__code=8)  # Nota de Crédito B
    credit_note.related_receipts.add(receipt)
    credit_note.save()

    credit_note.validate(raise_=True)
    assert credit_note.receipt_number is not None


@pytest.mark.django_db()
@pytest.mark.live()
def test_failed_validation(populated_db):
    """Test validating valid receipts."""
    receipt = ReceiptWithInconsistentVatAndTaxFactory()

    errs = receipt.validate()

    assert len(errs) == 1
    # FIXME: We're not creating rejection entries
    # assert receipt.validation.result == models.ReceiptValidation.RESULT_REJECTED
    assert models.ReceiptValidation.objects.count() == 0


@pytest.mark.django_db()
@pytest.mark.live()
def test_raising_failed_validation(populated_db):
    """Test validating valid receipts."""
    receipt = ReceiptWithInconsistentVatAndTaxFactory()

    with pytest.raises(
        exceptions.ValidationError,
        # Note: AFIP apparently edited this message and added a typo:
        match="DocNro 203012345 no se encuentra registrado en los padrones",
    ):
        receipt.validate(raise_=True)

    # FIXME: We're not creating rejection entries
    # assert receipt.validation.result == models.ReceiptValidation.RESULT_REJECTED
    assert models.ReceiptValidation.objects.count() == 0


@pytest.mark.django_db()
@pytest.mark.live()
def test_fetch_existing_data(populated_db):
    pos = models.PointOfSales.objects.first()
    rt = models.ReceiptType.objects.get(code=6)
    # last receipt number is needed for testing, it seems they flush old receipts
    # so we can't use a fixed receipt number
    last_receipt_number = models.Receipt.objects.fetch_last_receipt_number(pos, rt)
    receipt = models.Receipt.objects.fetch_receipt_data(
        receipt_type=6,
        receipt_number=last_receipt_number,
        point_of_sales=pos,
    )

    assert receipt.CbteDesde == last_receipt_number
    assert receipt.PtoVta == pos.number


@pytest.mark.django_db()
@pytest.mark.live()
def test_revalidation_valid_receipt(populated_db):
    """Test revalidation process of a valid receipt."""
    receipt = factories.ReceiptWithVatAndTaxFactory()
    receipt.validate()
    receipt.refresh_from_db()

    old_cae = receipt.validation.cae
    old_validation_pk = receipt.validation.id

    receipt.validation.delete()

    receipt.refresh_from_db()
    assert not receipt.is_validated

    validation = receipt.revalidate()

    assert validation is not None
    assert validation.receipt == receipt
    assert old_cae == validation.cae
    assert old_validation_pk != validation.id


@pytest.mark.live()
def test_revalidation_invalid_receipt(populated_db):
    """Test revalidation process of an invalid receipt. (Unexistent receipt)"""
    receipt = factories.ReceiptWithVatAndTaxFactory()
    next_num = (
        models.Receipt.objects.fetch_last_receipt_number(
            receipt.point_of_sales,
            receipt.receipt_type,
        )
        + 1
    )

    receipt.receipt_number = next_num
    receipt.save()

    receipt.refresh_from_db()

    validation = receipt.revalidate()

    assert validation is None


@pytest.mark.django_db()
def test_receipt_revalidate_without_receipt_number():
    """Test revalidation process of an invalid receipt. (Receipt without number)"""
    factories.PointOfSalesFactory()
    receipt = factories.ReceiptWithVatAndTaxFactory()
    receipt.refresh_from_db()

    validation = receipt.revalidate()

    assert validation is None


@pytest.mark.django_db()
def test_receipt_is_validated_when_not_validated():
    receipt = ReceiptFactory()
    assert not receipt.is_validated


@pytest.mark.django_db()
def test_receipt_is_validated_when_validated():
    receipt = ReceiptWithApprovedValidation()
    assert receipt.is_validated


@pytest.mark.django_db()
def test_receipt_is_validted_when_failed_validation():
    # These should never really exist,but oh well:
    receipt = ReceiptFactory(receipt_number=None)
    ReceiptValidationFactory(
        receipt=receipt,
        result=models.ReceiptValidation.RESULT_REJECTED,
    )
    assert not receipt.is_validated

    receipt = ReceiptFactory(receipt_number=1)
    ReceiptValidationFactory(
        receipt=receipt,
        result=models.ReceiptValidation.RESULT_REJECTED,
    )
    assert not receipt.is_validated


@pytest.mark.django_db()
def test_default_currency_no_currencies():
    receipt = models.Receipt()
    with pytest.raises(models.CurrencyType.DoesNotExist):
        receipt.currency


@pytest.mark.django_db()
def test_default_currency_multieple_currencies():
    c1 = factories.CurrencyTypeFactory(pk=2)
    c2 = factories.CurrencyTypeFactory(pk=1)
    c3 = factories.CurrencyTypeFactory(pk=3)

    receipt = models.Receipt()

    assert receipt.currency != c1
    assert receipt.currency == c2
    assert receipt.currency != c3


@pytest.mark.django_db()
def test_total_vat_no_vat():
    receipt = ReceiptFactory()

    assert receipt.total_vat == 0


@pytest.mark.django_db()
def test_total_vat_multiple_vats():
    receipt = ReceiptFactory()
    factories.VatFactory(receipt=receipt)
    factories.VatFactory(receipt=receipt)

    assert receipt.total_vat == 42


@pytest.mark.live()
def test_revalidation_validated_receipt(populated_db):
    """Test revalidation process of a validated receipt."""
    receipt_validation = factories.ReceiptValidationFactory()

    revalidation = receipt_validation.receipt.revalidate()

    assert revalidation is not None
    assert revalidation == receipt_validation


@pytest.mark.django_db()
def test_total_vat_proper_filtering():
    receipt = ReceiptFactory()
    factories.VatFactory(receipt=receipt)
    factories.VatFactory()

    assert receipt.total_vat == 21


@pytest.mark.django_db()
def test_total_tax_no_tax():
    receipt = ReceiptFactory()

    assert receipt.total_tax == 0


@pytest.mark.django_db()
def test_total_tax_multiple_taxes():
    receipt = ReceiptFactory()
    factories.TaxFactory(receipt=receipt)
    factories.TaxFactory(receipt=receipt)

    assert receipt.total_tax == 18


@pytest.mark.django_db()
def test_total_tax_proper_filtering():
    receipt = ReceiptFactory()
    factories.TaxFactory(receipt=receipt)
    factories.TaxFactory()

    assert receipt.total_tax == 9


def test_currenty_type_success():
    currency_type = models.CurrencyType(code="011", description="Pesos Uruguayos")
    assert str(currency_type) == "Pesos Uruguayos (011)"


@pytest.mark.django_db()
@pytest.mark.live()
def test_populate_method(live_ticket):
    assert models.CurrencyType.objects.count() == 0
    models.CurrencyType.objects.populate()
    assert models.CurrencyType.objects.count() == 50


@pytest.mark.django_db()
def test_receipt_entry_without_discount():
    """
    Test ReceiptEntry.

    Ensures that total_price for a ReceiptEntry without a discount
    works correctly.
    """

    receipt_entry = factories.ReceiptEntryFactory(
        quantity=1,
        unit_price=50,
    )
    assert receipt_entry.total_price == 50


@pytest.mark.django_db()
def test_receipt_entry_with_valid_discount():
    """
    Test ReceiptEntry.

    Ensures that total_price for a ReceiptEntry with a valid
    discount works correctly.
    """

    receipt_entry = factories.ReceiptEntryFactory(
        quantity=1, unit_price=50, discount=10
    )
    assert receipt_entry.total_price == 40


@pytest.mark.django_db()
def test_receipt_entry_negative_discount():
    """
    Test ReceiptEntry negative discount.

    Ensures that attempting to generate a ReceiptEntry with a negative discount
    raises.
    """

    with pytest.raises(Exception, match=r"\bdiscount_positive_value\b"):
        factories.ReceiptEntryFactory(quantity=5, unit_price=10, discount=-3)


@pytest.mark.django_db()
def test_receipt_entry_gt_total_discount():
    """
    Test ReceiptEntry discount greater than total price.

    Ensures that attempting to generate a ReceiptEntry with a discount
    greater than the total price before discount raises.
    """

    with pytest.raises(Exception, match=r"\bdiscount_less_than_total\b"):
        factories.ReceiptEntryFactory(quantity=1, unit_price=1, discount=2)
