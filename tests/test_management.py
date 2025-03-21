from __future__ import annotations

import pytest
from django.core import management

from django_afip.models import ClientVatCondition
from django_afip.models import GenericAfipType


@pytest.mark.django_db
def test_afip_metadata_command() -> None:
    assert len(GenericAfipType.SUBCLASSES) == 7

    for model in GenericAfipType.SUBCLASSES:
        # TYPING: mypy doesn't know about `.objects`.
        assert model.objects.count() == 0  # type: ignore[attr-defined]

    management.call_command("afipmetadata")

    for model in GenericAfipType.SUBCLASSES:
        # TYPING: mypy doesn't know about `.objects`.
        assert model.objects.count() > 0  # type: ignore[attr-defined]


@pytest.mark.django_db
def test_call_load_metadata_populate_client_vat_condition() -> None:
    """Test that load_metadata and populate methods work correctly."""

    assert ClientVatCondition.objects.count() == 0
    management.call_command("afipmetadata")

    assert ClientVatCondition.objects.count() == 11
