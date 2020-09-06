from pathlib import Path

import pytest


@pytest.fixture
def base_path() -> Path:
    return Path(__file__).resolve().parent


@pytest.fixture
def expired_crt(base_path) -> str:
    with open(base_path.joinpath("test_expired.crt")) as crt:
        return crt.read()


@pytest.fixture
def expired_key(base_path) -> str:
    with open(base_path.joinpath("test_expired.key")) as key:
        return key.read()
