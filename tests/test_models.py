from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import call
from unittest.mock import patch
import django

import pytest
from django.utils.timezone import make_aware
from pytest_django.asserts import assertQuerysetEqual

from django_afip import exceptions
from django_afip import factories
from django_afip import models
from django_afip.factories import CaeaFactory
from django_afip.factories import ReceiptFactory
from django_afip.factories import ReceiptValidationFactory
from django_afip.factories import ReceiptWithApprovedValidation
from django_afip.factories import ReceiptWithInconsistentVatAndTaxFactory
from django_afip.factories import ReceiptWithVatAndTaxFactory
from django_afip.factories import SubFactory
from django_afip.factories import TaxPayerFactory


def test_default_receipt_queryset():
    assert isinstance(models.Receipt.objects.all(), models.ReceiptQuerySet)


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
@pytest.mark.live
def test_validate_invoice(populated_db):
    """Test validating valid receipts."""

    receipt = ReceiptWithVatAndTaxFactory()
    errs = receipt.validate()

    assert len(errs) == 0
    assert receipt.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.live
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


@pytest.mark.django_db
@pytest.mark.live
def test_failed_validation(populated_db):
    """Test validating valid receipts."""
    receipt = ReceiptWithInconsistentVatAndTaxFactory()

    errs = receipt.validate()

    assert len(errs) == 1
    # FIXME: We're not creating rejection entries
    # assert receipt.validation.result == models.ReceiptValidation.RESULT_REJECTED
    assert models.ReceiptValidation.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.live
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


@pytest.mark.django_db
@pytest.mark.live
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


@pytest.mark.django_db
@pytest.mark.live
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


@pytest.mark.live
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


@pytest.mark.django_db
def test_receipt_revalidate_without_receipt_number():
    """Test revalidation process of an invalid receipt. (Receipt without number)"""
    factories.PointOfSalesFactory()
    receipt = factories.ReceiptWithVatAndTaxFactory()
    receipt.refresh_from_db()

    validation = receipt.revalidate()

    assert validation is None


@pytest.mark.django_db
def test_receipt_is_validated_when_not_validated():
    receipt = ReceiptFactory()
    assert not receipt.is_validated


@pytest.mark.django_db
def test_receipt_is_validated_when_validated():
    receipt = ReceiptWithApprovedValidation()
    assert receipt.is_validated


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_default_currency_no_currencies():
    receipt = models.Receipt()
    with pytest.raises(models.CurrencyType.DoesNotExist):
        receipt.currency


@pytest.mark.django_db
def test_default_currency_multieple_currencies():
    c1 = factories.CurrencyTypeFactory(pk=2)
    c2 = factories.CurrencyTypeFactory(pk=1)
    c3 = factories.CurrencyTypeFactory(pk=3)

    receipt = models.Receipt()

    assert receipt.currency != c1
    assert receipt.currency == c2
    assert receipt.currency != c3


@pytest.mark.django_db
def test_total_vat_no_vat():
    receipt = ReceiptFactory()

    assert receipt.total_vat == 0


@pytest.mark.django_db
def test_total_vat_multiple_vats():
    receipt = ReceiptFactory()
    factories.VatFactory(receipt=receipt)
    factories.VatFactory(receipt=receipt)

    assert receipt.total_vat == 42


@pytest.mark.live
def test_revalidation_validated_receipt(populated_db):
    """Test revalidation process of a validated receipt."""
    receipt_validation = factories.ReceiptValidationFactory()

    revalidation = receipt_validation.receipt.revalidate()

    assert revalidation is not None
    assert revalidation == receipt_validation


@pytest.mark.django_db
def test_total_vat_proper_filtering():
    receipt = ReceiptFactory()
    factories.VatFactory(receipt=receipt)
    factories.VatFactory()

    assert receipt.total_vat == 21


@pytest.mark.django_db
def test_total_tax_no_tax():
    receipt = ReceiptFactory()

    assert receipt.total_tax == 0


@pytest.mark.django_db
def test_total_tax_multiple_taxes():
    receipt = ReceiptFactory()
    factories.TaxFactory(receipt=receipt)
    factories.TaxFactory(receipt=receipt)

    assert receipt.total_tax == 18


@pytest.mark.django_db
def test_total_tax_proper_filtering():
    receipt = ReceiptFactory()
    factories.TaxFactory(receipt=receipt)
    factories.TaxFactory()

    assert receipt.total_tax == 9


def test_currenty_type_success():
    currency_type = models.CurrencyType(code="011", description="Pesos Uruguayos")
    assert str(currency_type) == "Pesos Uruguayos (011)"


@pytest.mark.django_db
@pytest.mark.live
def test_populate_method(live_ticket):
    assert models.CurrencyType.objects.count() == 0
    models.CurrencyType.objects.populate()
    assert models.CurrencyType.objects.count() == 50


@pytest.mark.django_db
def test_caea_creation():
    caea = factories.CaeaFactory()

    assert len(str(caea.caea_code)) == 14
    assert str(caea.caea_code) == "12345678974125"


@pytest.mark.django_db
def test_caea_creation_should_fail():

    with pytest.raises(
        ValueError,
        match="Field 'caea_code' expected a number but got 'A234567897412B'.",
    ):
        caea = factories.CaeaFactory(caea_code="A234567897412B")


@pytest.mark.django_db
@pytest.mark.live
def test_caea_creation_live(populated_db):

    caea = models.Caea.objects.first()

    assert len(str(caea.caea_code)) == 14
    assert str(caea.period) == datetime.today().strftime("%Y%m")


@pytest.mark.django_db
@pytest.mark.live
def test_create_caea_counter(populated_db):

    receipt_type = models.ReceiptType.objects.get(code=6)
    pos = factories.PointOfSalesFactoryCaea()
    number = None
    with pytest.raises(
        models.CaeaCounter.DoesNotExist,
    ):
        number = models.CaeaCounter.objects.get(
            pos=pos, receipt_type=receipt_type
        ).next_value

    assert number == None

    # caea = factories.CaeaFactory()
    caea = models.Caea.objects.get(pk=1)
    receipt = factories.ReceiptFactory(point_of_sales=pos)
    number = models.CaeaCounter.objects.get(
        pos=pos, receipt_type=receipt_type
    ).next_value
    assert number == 2


@pytest.mark.django_db
def test_create_receipt_caea():

    pos = factories.PointOfSalesFactoryCaea()
    caea = factories.CaeaFactory()
    # caea = models.Caea.objects.get(pk=1)
    pos_caea = models.PointOfSales.objects.all().filter(issuance_type="CAEA")
    receipt = factories.ReceiptFactory(point_of_sales=pos)

    assert len(pos_caea) == 1
    assert receipt.point_of_sales.issuance_type == "CAEA"
    assert str(receipt.caea.caea_code) == caea.caea_code
    assert receipt.receipt_number == 1


@pytest.mark.django_db
def test_two_caea_unique_constraint_should_fail():
    """
    Test that 2 caea with same order,period and taxpayer cannot be created
    """

    pos = factories.PointOfSalesFactoryCaea()
    caea = factories.CaeaFactory()
    with pytest.raises(
        django.db.utils.IntegrityError,
    ):
        caea2 = factories.CaeaFactory(caea_code="12345678912346")


@pytest.mark.django_db
def test_caea_reverse_relation_receipts():

    pos = factories.PointOfSalesFactoryCaea()
    caea = factories.CaeaFactory()
    # caea = models.Caea.objects.get(pk=1)
    receipt_1 = factories.ReceiptFactory(point_of_sales=pos)
    receipt_2 = factories.ReceiptFactory(point_of_sales=pos)
    assert receipt_1 != receipt_2

    receipts_with_caea = caea.receipts.all()
    assert receipt_1 and receipt_2 in receipts_with_caea
    assert len(receipts_with_caea) == 2
    assert receipt_1.receipt_number == 1
    assert receipt_2.receipt_number == 2


@pytest.mark.django_db
@pytest.mark.live
def test_validate_caea_receipt(populated_db):

    manager = models.ReceiptManager()
    receipt_type = models.ReceiptType.objects.get(code=6)
    pos = factories.PointOfSalesFactoryCaea()
    # caea = factories.CaeaFactory()
    caea = models.Caea.objects.get(pk=1)
    last_number = manager.fetch_last_receipt_number(
        point_of_sales=pos, receipt_type=receipt_type
    )
    caea_counter = models.CaeaCounter.objects.get_or_create(
        pos=pos, receipt_type=receipt_type
    )[0]
    caea_counter.next_value = last_number + 1
    caea_counter.save()

    receipt_1 = factories.ReceiptWithVatAndTaxFactoryCaea(point_of_sales=pos)

    errs = receipt_1.validate()

    assert len(errs) == 0
    assert receipt_1.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.live
def test_validate_caea_receipt_another_pos(populated_db):

    manager = models.ReceiptManager()
    receipt_type = models.ReceiptType.objects.get(code=6)
    pos = factories.PointOfSalesFactoryCaea()
    # caea = factories.CaeaFactory()
    caea = models.Caea.objects.get(pk=1)
    last_number = manager.fetch_last_receipt_number(
        point_of_sales=pos, receipt_type=receipt_type
    )
    caea_counter = models.CaeaCounter.objects.get_or_create(
        pos=pos, receipt_type=receipt_type
    )[0]
    caea_counter.next_value = last_number + 1
    caea_counter.save()

    receipt_1 = factories.ReceiptWithVatAndTaxFactoryCaea(point_of_sales=pos)
    receipt_2 = factories.ReceiptWithVatAndTaxFactoryCaea(point_of_sales=pos)

    caea_counter = models.CaeaCounter.objects.get_or_create(
        pos=pos, receipt_type=receipt_type
    )[0]
    assert receipt_1 != receipt_2
    assert (caea_counter.next_value - 2) == receipt_1.receipt_number
    assert (caea_counter.next_value - 1) == receipt_2.receipt_number

    qs = models.Receipt.objects.filter(point_of_sales=pos).filter(
        validation__isnull=True
    )
    errs = qs.validate()

    assert len(errs) == 0
    assert receipt_1.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert receipt_2.validation.result == models.ReceiptValidation.RESULT_APPROVED
    assert models.ReceiptValidation.objects.count() == 2


@pytest.mark.django_db
@pytest.mark.live
def test_validate_credit_note_caea(populated_db):

    """Test validating valid receipts."""
    # fetch data from afip to set the receipt number
    manager = models.ReceiptManager()
    receipt_type_fact = models.ReceiptType.objects.get(code=6)
    receipt_type_cn = models.ReceiptType.objects.get(code=8)
    pos = factories.PointOfSalesFactoryCaea()
    # caea = factories.CaeaFactory()
    caea = models.Caea.objects.get(pk=1)
    last_number = manager.fetch_last_receipt_number(
        point_of_sales=pos, receipt_type=receipt_type_fact
    )
    caea_counter_fact = models.CaeaCounter.objects.get_or_create(
        pos=pos, receipt_type=receipt_type_fact
    )[0]
    caea_counter_fact.next_value = last_number + 1
    caea_counter_fact.save()

    last_number = manager.fetch_last_receipt_number(
        point_of_sales=pos, receipt_type=receipt_type_cn
    )
    caea_counter_cn = models.CaeaCounter.objects.get_or_create(
        pos=pos, receipt_type=receipt_type_cn
    )[0]
    caea_counter_cn.next_value = last_number + 1
    caea_counter_cn.save()

    # Create a receipt (this credit note relates to it):
    receipt = factories.ReceiptWithVatAndTaxFactoryCaea(point_of_sales=pos)
    errs = receipt.validate()
    assert len(errs) == 0

    # Create a credit note for the above receipt:
    credit_note = ReceiptWithVatAndTaxFactory(
        receipt_type__code=8, point_of_sales=pos
    )  # Nota de Crédito B
    credit_note.related_receipts.add(receipt)
    credit_note.save()

    caea_counter_cn = models.CaeaCounter.objects.get_or_create(
        pos=pos, receipt_type=receipt_type_cn
    )[0]
    credit_note.validate(raise_=True)
    assert credit_note.receipt_number == (caea_counter_cn.next_value - 1)
    assert credit_note.validation.result == models.ReceiptValidation.RESULT_APPROVED


@pytest.mark.django_db
@pytest.mark.live
def test_inform_caea_without_movement(populated_db):
    pos = factories.PointOfSalesFactoryCaea()
    caea = models.Caea.objects.get(pk=1)
    payer = factories.TaxPayerFactory()

    resp = payer.consult_caea_without_operations(pos=pos, caea=caea)
    assert isinstance(resp, models.InformedCaeas)


@pytest.mark.django_db
@pytest.mark.live
def test_creation_informedcaea(populated_db):
    pos = factories.PointOfSalesFactoryCaea()
    caea = models.Caea.objects.get(pk=1)
    payer = factories.TaxPayerFactory()

    with pytest.raises(
        models.InformedCaeas.DoesNotExist,
    ):
        informed_caea = models.InformedCaeas.objects.get(pos=pos, caea=caea)

    payer.consult_caea_without_operations(pos=pos, caea=caea)
    informed_caea = models.InformedCaeas.objects.get(pos=pos, caea=caea)
    assert informed_caea.pk == 1
    assert informed_caea.caea == caea
    assert informed_caea.pos == pos


@pytest.mark.django_db
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


@pytest.mark.django_db
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


@pytest.mark.django_db
def test_receipt_entry_negative_discount():
    """
    Test ReceiptEntry negative discount.

    Ensures that attempting to generate a ReceiptEntry with a negative discount
    raises.
    """

    with pytest.raises(Exception, match=r"\bdiscount_positive_value\b"):
        factories.ReceiptEntryFactory(quantity=5, unit_price=10, discount=-3)


@pytest.mark.django_db
def test_receipt_entry_gt_total_discount():
    """
    Test ReceiptEntry discount greater than total price.

    Ensures that attempting to generate a ReceiptEntry with a discount
    greater than the total price before discount raises.
    """

    with pytest.raises(Exception, match=r"\bdiscount_less_than_total\b"):
        factories.ReceiptEntryFactory(quantity=1, unit_price=1, discount=2)


@pytest.mark.django_db
@pytest.mark.este
def test_bad_retrive_caea():
    """
    Test that in the way that the CAEA is assigned in the save signal even if
    there are multiple taxpayer with 1 CAEA each the code assigned well.

    It not ensure that if the same taxpayer has multiples actives CAEAs the correct will be assigned

    """
    caea_good = CaeaFactory()
    caea_bad = CaeaFactory(
        caea_code="12345678974188",
        valid_since=make_aware(datetime(2022, 5, 15)),
        expires=make_aware(datetime(2022, 5, 30)),
        generated=make_aware(datetime(2022, 5, 30, 21, 6, 4)),
        taxpayer=TaxPayerFactory(
            name="Jane Doe",
            cuit=20366642330,
        ),
    )

    pos = factories.PointOfSalesFactoryCaea()
    receipt = factories.ReceiptFactory(point_of_sales=pos)

    assert caea_bad.caea_code != receipt.caea.caea_code


@pytest.mark.django_db
@pytest.mark.este
def test_caea_assigned_receipt_correct():
    """
    Test that even if a taxpayer has multiples actives CAEAs the correct will be assigned
    """
    caea_good = CaeaFactory()
    caea_bad = CaeaFactory(
        caea_code="12345678974188",
        period=202209,
        order="1",
        valid_since=make_aware(datetime(2022, 4, 15)),
        expires=make_aware(datetime(2022, 4, 30)),
        generated=make_aware(datetime(2022, 4, 14, 21, 6, 4)),
    )

    assert caea_bad != caea_good

    pos = factories.PointOfSalesFactoryCaea()
    receipt = factories.ReceiptFactory(point_of_sales=pos)

    assert caea_bad.caea_code != receipt.caea.caea_code
    assert (
        models.Caea.objects.all()
        .filter(active=True, taxpayer=receipt.point_of_sales.owner)
        .count()
        == 2
    )

@pytest.mark.django_db
@pytest.mark.este
def test_ordering_receipts_work():

    receipt_1 = ReceiptFactory()
    receipt_2 = ReceiptFactory()
    receipt_3 = ReceiptFactory()

    assert models.Receipt.objects.last() == receipt_3
