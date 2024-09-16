from __future__ import annotations

from pathlib import Path

import pytest

from django_afip import crypto


@pytest.fixture
def signed_data() -> bytes:
    path = Path(__file__).parent / "signed_data.bin"
    with open(path, "rb") as data:
        return data.read()


def test_pkcs7_signing(
    expired_key: bytes,
    expired_crt: bytes,
    signed_data: bytes,
) -> None:
    # Use an expired cert here since this won't change on a yearly basis.
    data = b"Some data."

    actual_data = crypto.create_embeded_pkcs7_signature(data, expired_crt, expired_key)

    # Data after this index DOES vary depending on current time and other settings:
    assert actual_data[64:1100] == signed_data[64:1100]
    assert 1717 <= len(actual_data) <= 1790
