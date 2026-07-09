from enum import StrEnum, auto

# =========================
# Infrastructure Errors
# =========================


class InfrastructureErrorCode(StrEnum):
    """Enumerates infrastructure failure error codes.
    Attributes:
        `UNKNOWN_ERROR` (str):
            - Used when an unclassified or unexpected infrastructure
              failure occurs.
        `DATABASE_ERROR` (str):
            - Indicates a failure during database persistence or connection
              operations.
        `PASSWORD_HASHER_ERROR` (str):
            - Represents an error inside the password hashing and
              verification service.
        `AUTH_TOKEN_ERROR` (str):
            - Indicates a failure during cryptographic token generation,
              signing, or processing.
        `CORRUPTED_PERSISTENCE_STATE_ERROR` (str):
            - Raised when the retrieved database data cannot be successfully
              mapped into valid domain objects.
    """

    UNKNOWN_ERROR = auto()
    DATABASE_ERROR = auto()
    PASSWORD_HASHER_ERROR = auto()
    AUTH_TOKEN_ERROR = auto()
    CORRUPTED_PERSISTENCE_STATE_ERROR = auto()


class InfrastructureError(Exception):
    """Represents unexpected infrastructure-level failures.

    Used for unexpected errors raised by output adapters or
    external systems such as databases, email providers,
    caches, queues, or JWT libraries.

    Args:
        `message` (str):
            - Human-readable error description.
        `code` (InfrastructureErrorCode):
            - Infrastructure error code.
        `cause` (Exception | None):
            - Original raised exception.
    """

    def __init__(
        self,
        message: str,
        code: InfrastructureErrorCode = InfrastructureErrorCode.UNKNOWN_ERROR,
        cause: Exception | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.cause = cause


class CorruptedPersistenceStateError(InfrastructureError):
    """
    Raised when persisted data cannot be reconstructed
    into valid domain objects.

    This usually indicates that the persistence layer
    contains invalid, inconsistent, or corrupted data.

    Args:
        `cause` (Exception | None):
            - Original raised exception.
    """

    def __init__(self, cause: Exception | None = None):
        super().__init__(
            message=(
                'Persisted data is invalid and could not '
                'be reconstructed into domain objects'
            ),
            code=InfrastructureErrorCode.CORRUPTED_PERSISTENCE_STATE_ERROR,
            cause=cause,
        )


# =========================
# Application Base Errors
# =========================


class ApplicationError(Exception):
    """Base exception for application-level errors.

    Represents expected business or orchestration failures
    exposed by application use cases.

    Args:
        `message` (str):
            - Human-readable error description.
        `code` (str):
            - Stable machine-readable error identifier.
    """

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code
        self.message = message


# =========================
# User Errors
# =========================


class EmailAlreadyUsedError(ApplicationError):
    """Raised when email is already associated with an account."""

    def __init__(self):
        super().__init__(
            message='An account with this email already exists',
            code='EMAIL_ALREADY_USE',
        )


class UserNotFoundError(ApplicationError):
    """Raised when user does not exist."""

    def __init__(self):
        super().__init__(
            message='User not found',
            code='USER_NOT_FOUND',
        )


# =========================
# Verification Code Errors
# =========================


class VerificationCodeNotFoundError(ApplicationError):
    """Raised when verification code does not exist."""

    def __init__(self):
        super().__init__(
            message='Verification code not found',
            code='VERIFICATION_CODE_NOT_FOUND',
        )


# =========================
# Authentication Errors
# =========================


class PasswordMismatchError(ApplicationError):
    """Raised when passwords do not match."""

    def __init__(self):
        super().__init__(
            message='Passwords do not match',
            code='PASSWORD_MISMATCH',
        )


class InvalidCredentialsError(ApplicationError):
    """Raised when authentication credentials are invalid."""

    def __init__(self):
        super().__init__(
            message='Invalid email or password',
            code='INVALID_CREDENTIALS',
        )


# =========================
# Token Errors
# =========================


class InvalidTokenErrorCode(StrEnum):
    """Enumerates token validation error codes.

    Attributes:
        `TOKEN_EXPIRED` (str):
            - Indicates that the validation failed because the token
              has expired.
        `TOKEN_INVALID_SIGNATURE` (str):
            - Indicates that the cryptographic signature of the token
              is invalid.
        `TOKEN_MALFORMED` (str):
            - Indicates that the token structure does not follow the
              expected format.
        `TOKEN_INVALID` (str):
            - Used for general token validation failures that do not match
              other codes.
    """

    TOKEN_EXPIRED = auto()
    TOKEN_INVALID_SIGNATURE = auto()
    TOKEN_MALFORMED = auto()
    TOKEN_INVALID = auto()


class InvalidTokenError(ApplicationError):
    """Raised when JWT token validation fails.

    Used for client-related token failures such as expiration,
    malformed payloads, invalid signatures, or invalid tokens.

    Args:
        `code` (InvalidTokenErrorCode):
            - Token validation failure type.
    """

    def __init__(self, code: InvalidTokenErrorCode):
        message_map = {
            InvalidTokenErrorCode.TOKEN_EXPIRED: 'Token has expired.',
            InvalidTokenErrorCode.TOKEN_INVALID_SIGNATURE: (
                'Token signature is invalid.'
            ),
            InvalidTokenErrorCode.TOKEN_MALFORMED: 'Token is malformed.',
            InvalidTokenErrorCode.TOKEN_INVALID: 'Token is invalid.',
        }

        super().__init__(message=message_map[code], code=code.value)


class TokenNotFoundError(ApplicationError):
    """Raised when token does not exist."""

    def __init__(self):
        super().__init__(
            message='Token not found',
            code='TOKEN_NOT_FOUND',
        )


class TokenRevokedError(ApplicationError):
    """Raised when token has been revoked."""

    def __init__(self):
        super().__init__(
            message='Token is revoked',
            code='TOKEN_REVOKED',
        )


class InvalidTokenTypeError(ApplicationError):
    """Raised when the token type does not match the expected type."""

    def __init__(self):
        super().__init__(
            message='Token type is incorrect for operation.',
            code='TOKEN_INCORRECT_TYPE',
        )
