from OpenSSL import crypto

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

    pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
    signcert = crypto.load_certificate(crypto.FILETYPE_PEM, cert)

    bio_in = crypto._new_mem_buf(data)
    pkcs7 = crypto._lib.PKCS7_sign(
        signcert._x509, pkey._pkey, crypto._ffi.NULL, bio_in, PKCS7_NOSIGS
    )
    bio_out = crypto._new_mem_buf()
    crypto._lib.i2d_PKCS7_bio(bio_out, pkcs7)
    signed_data = crypto._bio_to_string(bio_out)

    return signed_data
