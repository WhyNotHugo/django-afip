class DjangoAfipException(Exception):
    """Superclass for all exceptions explicitly thrown by this app."""


class AfipException(DjangoAfipException):
    """
    Wraps around errors returned by AFIP's WS.
    """

    def __init__(self, response):
        Exception.__init__(self, 'Error {}: {}'.format(
            response.Errors.Err[0].Code,
            response.Errors.Err[0].Msg,
        ))


class AuthenticationError(DjangoAfipException):
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


class CannotValidateTogether(DjangoAfipException):
    """
    Raised when attempting to validate receipts that cannot be validated
    together (eg: different receipt types, or different point of sales).
    """


class ValidationError(DjangoAfipException):
    """Raised when a single Receipt failed to validate with AFIP's WS."""
