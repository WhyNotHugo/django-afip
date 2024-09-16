from __future__ import annotations

import pytest

from django_afip.helpers import ServerStatus
from django_afip.helpers import get_server_status


@pytest.mark.live
def test_get_server_status_production() -> None:
    status = get_server_status(True)

    assert isinstance(status, ServerStatus)


@pytest.mark.live
def test_get_server_status_testing() -> None:
    status = get_server_status(False)

    assert isinstance(status, ServerStatus)


@pytest.mark.live
def test_server_status_is_true() -> None:
    server_status = ServerStatus(app=True, db=True, auth=True)

    assert server_status


@pytest.mark.live
def test_server_status_is_false() -> None:
    server_status = ServerStatus(app=False, db=False, auth=False)

    assert not server_status
