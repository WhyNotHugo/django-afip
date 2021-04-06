from functools import lru_cache

import pytest

from django_afip import models
from django_afip.exceptions import AuthenticationError
from django_afip.factories import TaxPayerFactory
from django_afip.factories import get_test_file
from django_afip.models import AuthTicket

_live_mode = False


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


@lru_cache(None)
def live_taxpayer_factory():
    assert _live_mode
    taxpayer = TaxPayerFactory(pk=1)
    return taxpayer


@lru_cache(None)
def live_ticket_factory():
    assert _live_mode
    try:
        return AuthTicket.objects.get_any_active("wsfe")
    except AuthenticationError as e:
        pytest.exit(f"Bailing due to failure authenticating with AFIP:\n{e}")
    # TODO: Save the ticket to disk, and try loading it.
    # Maybe set up an actual YAML serialisers and use that?


@pytest.fixture
def live_taxpayer(db):
    """Return a taxpayer usable with AFIP's test servers."""
    taxpayer = live_taxpayer_factory()
    taxpayer.save()
    return taxpayer


@pytest.fixture
def live_ticket(db, live_taxpayer):
    """Return an authentication ticket usable with AFIP's test servers."""
    ticket = live_ticket_factory()
    ticket.taxpayer = live_taxpayer
    ticket.save()
    return ticket


@pytest.fixture
def populated_db(db, live_ticket, live_taxpayer):
    """Populate the database with fixtures and a POS"""

    models.load_metadata()
    live_taxpayer.fetch_points_of_sales()
