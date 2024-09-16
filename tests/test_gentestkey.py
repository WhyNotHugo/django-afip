from __future__ import annotations

import os

import pytest

from django_afip import factories


@pytest.mark.skipif(os.environ.get("GENTESTCSR") is None, reason="not a test")
@pytest.mark.django_db
def test_generate_test_csr() -> None:
    """Generate a new test CSR (this is not really a test)

    Run this with:

        GENTESTCSR=yes tox -e py-sqlite -- -k test_generate_test_csr
    """

    # This one is used for most tests.
    taxpayer = factories.TaxPayerFactory(is_sandboxed=True)

    csr = taxpayer.generate_csr("wsfe")
    with open("test.csr", "wb") as f:
        f.write(csr.read())

    # This one is used for the `test_authentication_with_bad` test.
    taxpayer = factories.AlternateTaxpayerFactory(is_sandboxed=True)

    csr = taxpayer.generate_csr("wsfe")
    with open("test2.csr", "wb") as f:
        f.write(csr.read())
