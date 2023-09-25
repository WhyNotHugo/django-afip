from __future__ import annotations

from unittest.mock import patch

import pytest
import requests
from requests.exceptions import SSLError

from django_afip.clients import get_client


@pytest.mark.live()
def test_services_are_cached() -> None:
    service1 = get_client("wsfe", False)
    with patch.dict("django_afip.clients.WSDLS", values={}, clear=True):
        service2 = get_client("wsfe", False)

    assert service1 is service2


def test_inexisting_service() -> None:
    with pytest.raises(ValueError, match="Unknown service name, nonexistant"):
        get_client("nonexistant", False)


@pytest.mark.live()
def test_insecure_dh_hack_required() -> None:
    with pytest.raises(SSLError, match="SSL: DH_KEY_TOO_SMALL. dh key too small"):
        requests.get("https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL")
