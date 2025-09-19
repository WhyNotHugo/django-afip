from __future__ import annotations

from datetime import date
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from django import VERSION as DJANGO_VERSION
from django.db.models import DecimalField
from freezegun import freeze_time

if DJANGO_VERSION[0] < 5:
    from pytest_django.asserts import assertQuerysetEqual as assertQuerySetEqual
else:
    from pytest_django.asserts import assertQuerySetEqual

from django_afip import exceptions
from django_afip import factories
from django_afip import models
from django_afip.clients import TZ_AR
from django_afip.factories import ReceiptFactory
from django_afip.factories import ReceiptFCEAWithVatAndTaxFactory
from django_afip.factories import ReceiptFCEAWithVatTaxAndOptionalsFactory
from django_afip.factories import ReceiptValidationFactory
from django_afip.factories import ReceiptWithApprovedValidation
from django_afip.factories import ReceiptWithInconsistentVatAndTaxFactory
from django_afip.factories import ReceiptWithVatAndTaxFactory

if TYPE_CHECKING:
    from django.db.models import QuerySet

    from django_afip.models import ReceiptQuerySet


def test_default_receipt_queryset() -> None:
    assert isinstance(models.Receipt.objects.all(), models.ReceiptQuerySet)


@pytest.mark.django_db
def test_validate_validated() -> None:
    receipt = ReceiptWithApprovedValidation()
    # TYPING: mypy can't understand default querysets.
    qs: ReceiptQuerySet = models.Receipt.objects.filter(  # type: ignore[assignment]
        pk=receipt.pk,
    )
    ticket = MagicMock()

    with patch(
        "django_afip.models.ReceiptQuerySet._assign_numbers",
        spec=True,
    ) as mocked_assign_numbers:
        qs.validate(ticket)

    assert mocked_assign_numbers.call_count == 0


# TODO: Also another tests that checks that we only pass filtered-out receipts.


def test_default_receipt_manager() -> None:
    assert isinstance(models.Receipt.objects, models.ReceiptManager)


@pytest.mark.django_db
def test_validate_receipt() -> None:
    receipt = ReceiptFactory()
    ticket = MagicMock()
    ticket._called = False

    def fake_validate(qs: QuerySet, ticket: MagicMock) -> None:
        assertQuerySetEqual(qs, [receipt.pk], lambda r: r.pk)
        ticket._called = True

    with patch(
        "django_afip.models.ReceiptQuerySet.validate",
        fake_validate,
    ):
        receipt.validate(ticket)

    assert ticket._called is True


@pytest.mark.django_db
@pytest.mark.live
def test_validate_invoice(populated_db: None) -> None:
    """Test validating valid receipts."""

    receipt = ReceiptWithVatAndTaxFactory()
    errs = receipt.validate()

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.live
def test_skip_validated_invoice(populated_db: None) -> None:
    """
    Test validating receipt that was already validated.

    If a query set includes receipts that were already validated, those and only
    those should be skipped.
    """

    receipt = ReceiptWithVatAndTaxFactory()
    receipt2 = ReceiptWithVatAndTaxFactory()

    # Validate only the first receipt
    errs = receipt.validate()
    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1

    # Validate them both together, the first one should be skipped
    original_cae, original_receipt_number = (
        receipt.validation.cae,
        receipt.receipt_number,
    )
    qs: ReceiptQuerySet = models.Receipt.objects.filter(
        pk__in=[receipt.pk, receipt2.pk]
    )  # type: ignore[assignment]
    errs = qs.validate()
    assert len(errs) == 0
    assert models.ReceiptValidation.objects.count() == 2
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert receipt2.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert original_cae == receipt.validation.cae
    assert original_receipt_number == receipt.receipt_number


@pytest.mark.django_db
@pytest.mark.live
def test_validate_fcea_invoice(populated_db: None) -> None:
    """Test validating valid receipts."""
    receipt = ReceiptFCEAWithVatTaxAndOptionalsFactory(document_number=20054100605)
    errs = receipt.validate()

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.live
def test_fail_validate_fcea_invoice(populated_db: None) -> None:
    """Test case to ensure that an invalid FCEA invoice fails."""

    receipt = ReceiptFCEAWithVatAndTaxFactory()
    errs = receipt.validate()

    assert len(errs) == 1
    assert models.ReceiptValidation.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.live
def test_validate_credit_note(populated_db: None) -> None:
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


@pytest.mark.django_db
@pytest.mark.live
def test_failed_validation(populated_db: None) -> None:
    """Test validating valid receipts."""
    receipt = ReceiptWithInconsistentVatAndTaxFactory()

    errs = receipt.validate()

    assert len(errs) == 1
    # FIXME: We're not creating rejection entries
    # assert receipt.validation.result == models.ReceiptValidation.RESULT_REJECTED
    assert models.ReceiptValidation.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.live
def test_raising_failed_validation(populated_db: None) -> None:
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


@pytest.mark.django_db
@pytest.mark.live
def test_fetch_existing_data(populated_db: None) -> None:
    pos = models.PointOfSales.objects.first()
    assert pos is not None
    rt = models.ReceiptType.objects.get(code=6)
    # last receipt number is needed for testing, it seems they flush old receipts
    # so we can't use a fixed receipt number
    last_receipt_number = models.Receipt.objects.fetch_last_receipt_number(pos, rt)
    receipt = models.Receipt.objects.fetch_receipt_data(
        receipt_type="6",
        receipt_number=last_receipt_number,
        point_of_sales=pos,
    )

    assert receipt.CbteDesde == last_receipt_number
    assert receipt.PtoVta == pos.number


@pytest.mark.django_db
@pytest.mark.live
def test_revalidation_valid_receipt(populated_db: None) -> None:
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


@pytest.mark.live
def test_revalidation_invalid_receipt(populated_db: None) -> None:
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


@pytest.mark.django_db
def test_receipt_revalidate_without_receipt_number() -> None:
    """Test revalidation process of an invalid receipt. (Receipt without number)"""
    factories.PointOfSalesFactory()
    receipt = factories.ReceiptWithVatAndTaxFactory()
    receipt.refresh_from_db()

    validation = receipt.revalidate()

    assert validation is None


@pytest.mark.django_db
def test_receipt_is_validated_when_not_validated() -> None:
    receipt = ReceiptFactory()
    assert not receipt.is_validated


@pytest.mark.django_db
def test_receipt_is_validated_when_validated() -> None:
    receipt = ReceiptWithApprovedValidation()
    assert receipt.is_validated


@pytest.mark.django_db
def test_receipt_is_validated_when_failed_validation() -> None:
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


@pytest.mark.django_db
def test_default_currency_no_currencies() -> None:
    receipt = models.Receipt()
    with pytest.raises(models.CurrencyType.DoesNotExist):
        receipt.currency  # noqa: B018  # expression raises


@pytest.mark.django_db
def test_default_currency_multieple_currencies() -> None:
    c1 = factories.CurrencyTypeFactory(pk=2)
    c2 = factories.CurrencyTypeFactory(pk=1)
    c3 = factories.CurrencyTypeFactory(pk=3)

    receipt = models.Receipt()

    assert receipt.currency != c1
    assert receipt.currency == c2
    assert receipt.currency != c3


@pytest.mark.django_db
def test_total_vat_no_vat() -> None:
    receipt = ReceiptFactory()

    assert receipt.total_vat == 0


@pytest.mark.django_db
def test_total_vat_multiple_vats() -> None:
    receipt = ReceiptFactory()
    factories.VatFactory(receipt=receipt)
    factories.VatFactory(receipt=receipt)

    assert receipt.total_vat == 42


@pytest.mark.live
def test_revalidation_validated_receipt(populated_db: None) -> None:
    """Test revalidation process of a validated receipt."""
    receipt_validation = factories.ReceiptValidationFactory()

    revalidation = receipt_validation.receipt.revalidate()

    assert revalidation is not None
    assert revalidation == receipt_validation


@pytest.mark.django_db
def test_total_vat_proper_filtering() -> None:
    receipt = ReceiptFactory()
    factories.VatFactory(receipt=receipt)
    factories.VatFactory()

    assert receipt.total_vat == 21


@pytest.mark.django_db
def test_total_tax_no_tax() -> None:
    receipt = ReceiptFactory()

    assert receipt.total_tax == 0


@pytest.mark.django_db
def test_total_tax_multiple_taxes() -> None:
    receipt = ReceiptFactory()
    factories.TaxFactory(receipt=receipt)
    factories.TaxFactory(receipt=receipt)

    assert receipt.total_tax == 18


@pytest.mark.django_db
def test_total_tax_proper_filtering() -> None:
    receipt = ReceiptFactory()
    factories.TaxFactory(receipt=receipt)
    factories.TaxFactory()

    assert receipt.total_tax == 9


def test_currenty_type_success() -> None:
    currency_type = models.CurrencyType(code="011", description="Pesos Uruguayos")
    assert str(currency_type) == "Pesos Uruguayos (011)"


@pytest.mark.django_db
@pytest.mark.live
def test_populate_method(live_ticket: models.AuthTicket) -> None:
    assert models.CurrencyType.objects.count() == 0
    models.CurrencyType.objects.populate()
    assert models.CurrencyType.objects.count() == 49


@pytest.mark.django_db
def test_receipt_entry_without_discount() -> None:
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


@pytest.mark.django_db
def test_receipt_entry_with_valid_discount() -> None:
    """
    Test ReceiptEntry.

    Ensures that total_price for a ReceiptEntry with a valid
    discount works correctly.
    """

    receipt_entry = factories.ReceiptEntryFactory(
        quantity=1, unit_price=50, discount=10
    )
    assert receipt_entry.total_price == 40


@pytest.mark.django_db
def test_receipt_entry_negative_discount() -> None:
    """
    Test ReceiptEntry negative discount.

    Ensures that attempting to generate a ReceiptEntry with a negative discount
    raises.
    """

    with pytest.raises(Exception, match=r"\bdiscount_positive_value\b"):
        factories.ReceiptEntryFactory(quantity=5, unit_price=10, discount=-3)


@pytest.mark.django_db
def test_receipt_entry_gt_total_discount() -> None:
    """
    Test ReceiptEntry discount greater than total price.

    Ensures that attempting to generate a ReceiptEntry with a discount
    greater than the total price before discount raises.
    """

    with pytest.raises(Exception, match=r"\bdiscount_less_than_total\b"):
        factories.ReceiptEntryFactory(quantity=1, unit_price=1, discount=2)


def test_receipt_entry_has_quantity_decimal_field() -> None:
    """Test that ReceiptEntry quantity now is a DecimalField"""
    field = models.ReceiptEntry._meta.get_field("quantity")

    # Verifica que el campo ahora es de tipo DecimalField
    assert isinstance(field, DecimalField)
    assert field.max_digits == 15
    assert field.decimal_places == 2


@pytest.mark.django_db
def test_receipt_entry_manage_decimal_quantities() -> None:
    """
    Test that ReceiptEntry can manage a decimal quantity
    """
    factories.ReceiptEntryFactory(quantity=Decimal("2"), unit_price=3.33)
    factories.ReceiptEntryFactory(quantity=Decimal("5.23"), unit_price=3.33)

    assert models.ReceiptEntry.objects.all().count() == 2

    first = models.ReceiptEntry.objects.first()
    assert first is not None
    assert first.quantity == Decimal("2")

    last = models.ReceiptEntry.objects.last()
    assert last is not None
    assert last.quantity == Decimal("5.23")


@pytest.mark.django_db
@freeze_time("2023-11-16 18:39:40")
def test_approximate_noop_today() -> None:
    today = datetime.now(TZ_AR).date()

    factories.ReceiptWithApprovedValidation(issued_date=today - timedelta(days=20))

    receipt = factories.ReceiptFactory(issued_date=today)
    changed = receipt.approximate_date()

    assert changed is False
    assert receipt.issued_date == today


@pytest.mark.django_db
@freeze_time("2023-11-16 18:39:40")
def test_approximate_noop_two_days_ago() -> None:
    today = datetime.now(TZ_AR).date()
    two_days_ago = date(2023, 11, 14)

    factories.ReceiptWithApprovedValidation(issued_date=today - timedelta(days=20))

    receipt = factories.ReceiptFactory(issued_date=two_days_ago)
    changed = receipt.approximate_date()

    assert changed is False
    assert receipt.issued_date == two_days_ago


@pytest.mark.django_db
@freeze_time("2023-11-16 18:39:40")
def test_approximate_date_today_with_most_recent() -> None:
    today = datetime.now(TZ_AR).date()

    factories.ReceiptWithApprovedValidation(issued_date=today)
    receipt = factories.ReceiptFactory(issued_date=today - timedelta(days=30))
    changed = receipt.approximate_date()

    assert changed is True
    assert receipt.issued_date == date(2023, 11, 16)


@pytest.mark.django_db
@freeze_time("2023-11-16 18:39:40")
def test_approximate_date_yesterday_with_most_recent() -> None:
    today = datetime.now(TZ_AR).date()

    factories.ReceiptWithApprovedValidation(issued_date=today - timedelta(days=1))

    receipt = factories.ReceiptFactory(issued_date=today - timedelta(days=30))
    changed = receipt.approximate_date()

    assert changed is True
    assert receipt.issued_date == date(2023, 11, 15)


@pytest.mark.django_db
@freeze_time("2023-11-16 18:39:40")
def test_approximate_date_30_days_ago_with_most_recent_20_days_ago() -> None:
    today = datetime.now(TZ_AR).date()

    factories.ReceiptWithApprovedValidation(issued_date=today - timedelta(days=20))

    receipt = factories.ReceiptFactory(issued_date=today - timedelta(days=30))
    changed = receipt.approximate_date()

    assert changed is True
    assert receipt.issued_date == date(2023, 11, 11)


@pytest.mark.django_db
@freeze_time("2023-11-16 18:39:40")
def test_approximate_date_2_days_ago_with_most_recent_20_days_ago() -> None:
    today = datetime.now(TZ_AR).date()
    two_days_ago = date(2023, 11, 14)

    factories.ReceiptWithApprovedValidation(issued_date=today - timedelta(days=20))

    receipt = factories.ReceiptFactory(issued_date=two_days_ago)
    changed = receipt.approximate_date()

    assert changed is False
    assert receipt.issued_date == two_days_ago


@pytest.mark.django_db
@freeze_time("2023-11-16 18:39:40")
def test_approximate_date_two_days_ago_without_most_recent() -> None:
    two_days_ago = date(2023, 11, 14)

    receipt = factories.ReceiptFactory(issued_date=two_days_ago)
    changed = receipt.approximate_date()

    assert changed is False
    assert receipt.issued_date == two_days_ago


@pytest.mark.django_db
@freeze_time("2023-11-16 18:39:40")
def test_approximate_date_failure() -> None:
    one_month_ago = date(2023, 10, 16)

    receipt = factories.ReceiptWithApprovedValidation(issued_date=one_month_ago)

    with pytest.raises(
        exceptions.DjangoAfipException,
        match="Expected to update one receipt, updated 0\\.",
    ):
        receipt.approximate_date()


@pytest.mark.django_db
def test_client_vat_condition_fields() -> None:
    """Test that ClientVatCondition fields are properly set."""
    assert (
        len(models.ClientVatCondition._meta.fields) == 4
    )  # id, code, description, cmp_clase
    from django.db import models as django_models

    assert models.ClientVatCondition._meta.get_field("code").max_length == 3
    assert (
        models.ClientVatCondition._meta.get_field("code").__class__
        == django_models.CharField
    )
    assert models.ClientVatCondition._meta.get_field("description").max_length == 250
    assert (
        models.ClientVatCondition._meta.get_field("description").__class__
        == django_models.CharField
    )
    assert models.ClientVatCondition._meta.get_field("cmp_clase").max_length == 10
    assert (
        models.ClientVatCondition._meta.get_field("cmp_clase").__class__
        == django_models.CharField
    )


@pytest.mark.django_db
@pytest.mark.live
def test_client_vat_condition_populate(live_ticket: models.AuthTicket) -> None:
    """Test populating client VAT conditions from AFIP."""
    # Ensure we start with no client VAT conditions
    assert models.ClientVatCondition.objects.count() == 0
    models.ClientVatCondition.populate(ticket=live_ticket)
    assert models.ClientVatCondition.objects.count() == 11

    initial_count = models.ClientVatCondition.objects.count()
    models.ClientVatCondition.populate(ticket=live_ticket)
    assert models.ClientVatCondition.objects.count() == initial_count


@pytest.mark.django_db
def test_load_metadata() -> None:
    """Test populating AFIP models from fixtures."""
    fetched_models = [
        models.ClientVatCondition,
        models.ConceptType,
        models.CurrencyType,
        models.DocumentType,
        models.OptionalType,
        models.ReceiptType,
        models.TaxType,
        models.VatType,
    ]

    # At first we have no data
    for m in fetched_models:
        assert m.objects.count() == 0

    # Load data and expect data
    models.load_metadata()
    counts = []
    for m in fetched_models:
        assert m.objects.count() > 0
        counts.append(m.objects.count())

    # Load data again and expect no change
    models.load_metadata()
    for i, m in enumerate(fetched_models):
        assert m.objects.count() == counts[i]
