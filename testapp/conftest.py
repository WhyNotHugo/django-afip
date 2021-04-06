import pytest

from django_afip.factories import get_test_file


@pytest.fixture
def expired_crt() -> bytes:
    with open(get_test_file("test_expired.crt"), "rb") as crt:
        return crt.read()


@pytest.fixture
def expired_key() -> bytes:
    with open(get_test_file("test_expired.key"), "rb") as key:
        return key.read()
