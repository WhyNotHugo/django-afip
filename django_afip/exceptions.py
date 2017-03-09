from . import parsers


class AfipException(Exception):
    """
    Wraps around errors returned by AFIP's WS.
    """

    def __init__(self, response):
        Exception.__init__(self, 'Error {}: {}'.format(
            response.Errors.Err[0].Code,
            parsers.parse_string(response.Errors.Err[0].Msg),
        ))


class CertificateExpiredException(Exception):
    """
    Raised when an authentication was attempted with an expired
    certificate.
    """
    pass
