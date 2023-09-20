from __future__ import annotations

import pytest
from django.core import management

from django_afip.models import GenericAfipType


@pytest.mark.django_db()
def test_afip_metadata_command() -> None:
    assert len(GenericAfipType.SUBCLASSES) == 7

    for model in GenericAfipType.SUBCLASSES:
        assert model.objects.count() == 0

    management.call_command("afipmetadata")

    for model in GenericAfipType.SUBCLASSES:
        assert model.objects.count() > 0
