from decimal import Decimal

import pytest

from django_afip.factories import VatTypeFactory


@pytest.mark.django_db
def test_vat_type_as_decimal():
    assert VatTypeFactory().as_decimal == Decimal("0.21")
    assert VatTypeFactory(description="10.5%").as_decimal == Decimal("0.105")
    assert VatTypeFactory(description="0%").as_decimal == Decimal(0)
