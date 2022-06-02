from unittest.mock import patch

import pytest
from django.conf import settings
from django.core import serializers

from django_afip import models
from django_afip.exceptions import AuthenticationError
from django_afip.factories import TaxPayerFactory
from django_afip.factories import get_test_file
from django_afip.models import AuthTicket

CACHED_TICKET_PATH = settings.BASE_DIR / "test_ticket.yaml"
_live_mode = False


@pytest.fixture(autouse=True)
def disable_durability_check():
    with patch(
        "django_afip.models.ReceiptQuerySet._ensure_durability",
        False,
        spec=True,
    ):
        yield


def pytest_runtest_setup(item):
    """Set live mode if the marker has been passed to pytest.

    This avoid accidentally using any of the live-mode fixtures in non-live mode."""
    if list(item.iter_markers(name="live")):
        global _live_mode
        _live_mode = True


@pytest.fixture
def expired_crt() -> bytes:
    with open(get_test_file("test_expired.crt"), "rb") as crt:
        return crt.read()


@pytest.fixture
def expired_key() -> bytes:
    with open(get_test_file("test_expired.key"), "rb") as key:
        return key.read()


@pytest.fixture
def live_taxpayer(db):
    """Return a taxpayer usable with AFIP's test servers."""
    return TaxPayerFactory(pk=1)


@pytest.fixture
def live_ticket(db, live_taxpayer):
    """Return an authentication ticket usable with AFIP's test servers.

    AFIP doesn't allow requesting tickets too often, so we after a few runs
    of the test suite, we can't generate tickets any more and have to wait.

    This helper generates a ticket, and saves it to disk into the app's
    BASE_DIR, so that developers can run tests over and over without having to
    worry about the limitation.

    Expired tickets are not deleted or handled properly; it's up to you to
    delete stale cached tickets.

    When running in CI pipelines, this file will never be preset so won't be a
    problem.
    """
    assert _live_mode

    # Try reading a cached ticket from disk:
    try:
        with open(CACHED_TICKET_PATH) as f:
            [obj] = serializers.deserialize("yaml", f.read())
            obj.save()
    except FileNotFoundError:
        # If something failed, we should still have no tickets in the DB:
        assert models.AuthTicket.objects.count() == 0

    try:
        # Get a new ticket. If the one we just loaded is still valid, that one
        # will be returned, otherwise, a new one will be created.
        ticket = AuthTicket.objects.get_any_active("wsfe")
    except AuthenticationError as e:
        pytest.exit(f"Bailing due to failure authenticating with AFIP:\n{e}")

    # No matter how we go it, we must have at least one ticket in the DB:
    assert models.AuthTicket.objects.count() >= 1

    data = serializers.serialize("yaml", [ticket])
    with open(CACHED_TICKET_PATH, "w") as f:
        f.write(data)

    return ticket


@pytest.fixture
def populated_db(live_ticket, live_taxpayer):
    """Populate the database with fixtures and a POS"""

    models.load_metadata()
    live_taxpayer.fetch_points_of_sales()
