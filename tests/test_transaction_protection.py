from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from django_afip import models
from django_afip.factories import ReceiptFactory


@pytest.fixture()
def disable_durability_check():
    """Disable the global fixture of the same name."""


@pytest.mark.django_db()
def test_raises():
    """Calling ``validate`` inside a transaction should raise."""

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
        with pytest.raises(RuntimeError):
            queryset.validate(ticket)

    assert mocked_assign_numbers.call_count == 0
    assert mocked__validate.call_count == 0
    assert mocked__validate.call_args is None
