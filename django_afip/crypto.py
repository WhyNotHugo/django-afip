from __future__ import annotations

from typing import IO

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.serialization.pkcs7 import PKCS7Options
from cryptography.hazmat.primitives.serialization.pkcs7 import PKCS7SignatureBuilder
from cryptography.x509 import load_pem_x509_certificate
from OpenSSL import crypto

from django_afip import exceptions


def create_embeded_pkcs7_signature(data: bytes, cert: bytes, key: bytes) -> bytes:
    """Creates an embedded ("nodetached") PKCS7 signature.

    This is equivalent to the output of::

        openssl smime -sign -signer cert -inkey key -outform DER -nodetach < data
    """

    try:
        pkey = load_pem_private_key(key, None)
        signcert = load_pem_x509_certificate(cert)
    except Exception as e:
        raise exceptions.CorruptCertificate from e

    if not isinstance(pkey, RSAPrivateKey):
        raise exceptions.CorruptCertificate("Private key is not RSA")

    return (
        PKCS7SignatureBuilder()
        .set_data(data)
        .add_signer(signcert, pkey, hashes.SHA256())
        .sign(Encoding.DER, [PKCS7Options.Binary])
    )


def create_key(file_: IO[bytes]) -> None:
    """Create a key and write it into ``file_``."""
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    file_.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
    file_.flush()


def create_csr(
    key_file: IO[bytes],
    organization_name: str,
    common_name: str,
    serial_number: str,
    file_: IO[bytes],
) -> None:
    """Create a certificate signing request and write it into ``file_``."""
    key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_file.read())

    req = crypto.X509Req()
    subj = req.get_subject()

    subj.O = organization_name
    subj.CN = common_name
    subj.serialNumber = serial_number  # type: ignore[attr-defined]

    req.set_pubkey(key)
    req.sign(key, "md5")

    file_.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, req))
