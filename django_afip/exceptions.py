class AfipException(Exception):
    """
    Wraps around errors returned by AFIP's WS.
    """

    def __init__(self, response):
        Exception.__init__(self, 'Error {}: {}'.format(
            response.Errors.Err[0].Code,
            response.Errors.Err[0].Msg,
        ))


class AuthenticationError(Exception):
    """
    Raised when there is a non-specific error during an authentication attempt.
    """
    pass


class CertificateExpired(AuthenticationError):
    """
    Raised when an authentication was attempted with an expired certificate.
    """
    pass


class UntrustedCertificate(AuthenticationError):
    """
    Raise when an untrusted certificate is used in an authentication attempt.
    """
    pass


class CorruptCertificate(AuthenticationError):
    """
    Raised when a corrupt ceritificate file is used in an authenticaiton
    attempt.
    """
    pass
