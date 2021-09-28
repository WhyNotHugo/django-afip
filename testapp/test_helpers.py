import pytest

from django_afip.helpers import ServerStatus
from django_afip.helpers import get_server_status


@pytest.mark.live
def test_get_server_status_production():
    status = get_server_status(True)

    assert isinstance(status, ServerStatus)


@pytest.mark.live
def test_get_server_status_testing():
    status = get_server_status(False)

    assert isinstance(status, ServerStatus)
