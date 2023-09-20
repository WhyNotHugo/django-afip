from __future__ import annotations

import pytest
from django.core.management import call_command


@pytest.mark.django_db()
def test_no_missing_migrations() -> None:
    """Check that there are no missing migrations of the app."""

    # This returns pending migrations -- or false if non are pending.
    assert not call_command("makemigrations", check=True)
