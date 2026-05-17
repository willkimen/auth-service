from enum import StrEnum

# =========================
# Infrastructure Errors
# =========================


class InfrastructureErrorCode(StrEnum):
    """Enumerates infrastructure failure error codes."""

    UNKNOWN = 'INFRA_UNKNOWN_ERROR'
    DATABASE = 'INFRA_DATABASE_ERROR'
    PASSWORD_HASHER = 'INFRA_PASSWORD_HASHER_ERROR'
    AUTH_TOKEN = 'INFRA_AUTH_TOKEN_ERROR'
    CORRUPTED_PERSISTENCE_STATE = 'INFRA_CORRUPTED_PERSISTENCE_STATE'


class InfrastructureError(Exception):
    """Represents unexpected infrastructure-level failures.

    Used for unexpected errors raised by output adapters or
    external systems such as databases, email providers,
    caches, queues, or JWT libraries.

    Args:
        message (str): Human-readable error description.
        code (InfrastructureErrorCode): Infrastructure error code.
        cause (Exception | None): Original raised exception.
    """

    def __init__(
        self,
        message: str,
        code: InfrastructureErrorCode = InfrastructureErrorCode.UNKNOWN,
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
        message (str): Human-readable error description.
        code (InfrastructureErrorCode): Infrastructure error code.
        cause (Exception | None): Original raised exception.
    """

    def __init__(self, cause: Exception | None = None):
        super().__init__(
            message=(
                'Persisted data is invalid and could not '
                'be reconstructed into domain objects'
            ),
            code=InfrastructureErrorCode.CORRUPTED_PERSISTENCE_STATE,
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
        message (str): Human-readable error description.
        code (str): Stable machine-readable error identifier.
    """

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


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


class IncorrectPasswordError(ApplicationError):
    """Raised when provided password is incorrect."""

    def __init__(self):
        super().__init__(
            message='Incorrect password',
            code='INCORRECT_PASSWORD',
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


class TokenErrorCode(StrEnum):
    """Enumerates token validation error codes."""

    EXPIRED = 'TOKEN_EXPIRED'
    INVALID_SIGNATURE = 'TOKEN_INVALID_SIGNATURE'
    MALFORMED = 'TOKEN_MALFORMED'
    INVALID = 'TOKEN_INVALID'


class TokenError(ApplicationError):
    """Raised when JWT token validation fails.

    Used for client-related token failures such as expiration,
    malformed payloads, invalid signatures, or invalid tokens.

    Args:
        code (TokenErrorCode): Token validation failure type.
    """

    def __init__(self, code: TokenErrorCode):
        message_map = {
            TokenErrorCode.EXPIRED: 'Token has expired.',
            TokenErrorCode.INVALID_SIGNATURE: 'Token signature is invalid.',
            TokenErrorCode.MALFORMED: 'Token is malformed.',
            TokenErrorCode.INVALID: 'Token is invalid.',
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
