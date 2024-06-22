from __future__ import annotations


class DjangoAfipException(Exception):
    """Superclass for exceptions thrown by `django_afip`."""


class AfipException(DjangoAfipException):
    """Wraps around errors returned by AFIP's WS."""

    def __init__(self, response) -> None:  # noqa: ANN001
        if "Errors" in response:
            message = (
                f"Error {response.Errors.Err[0].Code}: {response.Errors.Err[0].Msg}"
            )
        else:
            message = (
                f"Error {response.errorConstancia.idPersona}: "
                f"{response.errorConstancia.error[0]}"
            )
        Exception.__init__(self, message)


class AuthenticationError(DjangoAfipException):
    """Raised when there is an error during an authentication attempt.

    Usually, subclasses of this error are raised, but for unexpected errors, this type
    may be raised.
    """


class CertificateExpired(AuthenticationError):
    """Raised when an authentication was attempted with an expired certificate."""


class UntrustedCertificate(AuthenticationError):
    """Raise when an untrusted certificate is used in an authentication attempt."""


class CorruptCertificate(AuthenticationError):
    """Raised when a corrupt certificate file is used in an authentication attempt."""


class CannotValidateTogether(DjangoAfipException):
    """Raised when attempting to validate invalid combinations of receipts.

    Receipts of different ``receipt_type`` or ``point_of_sales`` cannot be validated
    together.
    """


class ValidationError(DjangoAfipException):
    """Raised when a single Receipt failed to validate with AFIP's WS."""
