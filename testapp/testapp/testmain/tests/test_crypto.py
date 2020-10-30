import pytest

from django_afip import crypto


@pytest.fixture
def signed_data(base_path):
    with open(base_path.joinpath("signed_data.bin"), "rb") as data:
        return data.read()


def test_pkcs7_signing(expired_key: bytes, expired_crt: bytes, signed_data: bytes):
    # Use an expired cert here since this won't change on a yearly basis.
    data = b"Some data."

    actual_data = crypto.create_embeded_pkcs7_signature(data, expired_crt, expired_key)

    # Data after this index DOES vary depending on current time and other settings:
    assert actual_data[:1100] == signed_data[:1100]
    assert len(actual_data) == len(signed_data)
