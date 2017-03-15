from OpenSSL import crypto

from django_afip import exceptions

PKCS7_NOSIGS = 0x4  # defined in pkcs7.h


def create_embeded_pkcs7_signature(data, cert, key):
    """
    Creates an embeded ("nodetached") pkcs7 signature.

    This is equivalent to the output of::

        openssl smime -sign -signer cert -inkey key -outform DER -nodetach < data

    :type data: bytes
    :type cert: str
    :type key: str
    """  # noqa

    assert isinstance(data, bytes)
    assert isinstance(cert, str)

    try:
        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
        signcert = crypto.load_certificate(crypto.FILETYPE_PEM, cert)
    except crypto.Error as e:
        raise exceptions.CorruptCertificate from e

    bio_in = crypto._new_mem_buf(data)
    pkcs7 = crypto._lib.PKCS7_sign(
        signcert._x509, pkey._pkey, crypto._ffi.NULL, bio_in, PKCS7_NOSIGS
    )
    bio_out = crypto._new_mem_buf()
    crypto._lib.i2d_PKCS7_bio(bio_out, pkcs7)
    signed_data = crypto._bio_to_string(bio_out)

    return signed_data


def create_key(file_):
    """
    Create a key and save it into ``file_``.

    Note that ``file`` must be opened in binary mode.
    """
    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    file_.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))
    file_.flush()


def create_csr(key_file, organization_name, common_name, serial_number, file_):
    """Create a CSR for a key, and save it into ``file``."""
    key = crypto.load_privatekey(crypto.FILETYPE_PEM, key_file.read())

    req = crypto.X509Req()
    subj = req.get_subject()

    subj.O = organization_name
    subj.CN = common_name
    subj.serialNumber = serial_number

    req.set_pubkey(key)
    req.sign(key, 'md5')

    file_.write(crypto.dump_certificate_request(crypto.FILETYPE_PEM, req))
