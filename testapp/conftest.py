import pytest

from django_afip.factories import get_test_file


@pytest.fixture
def expired_crt() -> bytes:
    return get_test_file("test_expired.crt", "rb").read()


@pytest.fixture
def expired_key() -> bytes:
    return get_test_file("test_expired.key", "rb").read()
