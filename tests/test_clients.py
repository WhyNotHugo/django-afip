from unittest.mock import patch

import pytest

from django_afip.clients import get_client


@pytest.mark.live
def test_services_are_cached():
    service1 = get_client("wsfe", False)
    with patch.dict("django_afip.clients.WSDLS", values={}, clear=True):
        service2 = get_client("wsfe", False)

    assert service1 is service2


@pytest.mark.live
def test_inexisting_service():
    with pytest.raises(ValueError, match="Unknown service name, nonexistant"):
        get_client("nonexistant", False)
