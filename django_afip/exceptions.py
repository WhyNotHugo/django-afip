class DjangoAfipException(Exception):
    """Superclass for all exceptions explicitly thrown by this app."""


class AfipException(DjangoAfipException):
    """
    Wraps around errors returned by AFIP's WS.
    """

    def __init__(self, response):
        if "Errors" in response:
            message = "Error {}: {}".format(
                response.Errors.Err[0].Code,
                response.Errors.Err[0].Msg,
            )
        else:
            message = "Error {}: {}".format(
                response.errorConstancia.idPersona,
                response.errorConstancia.error[0],
            )
        Exception.__init__(self, message)


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


class CaeaCountError(DjangoAfipException):
    """Raised when query the caea to obtain the number but 0 or 2 or more."""
