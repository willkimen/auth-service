from enum import StrEnum, auto


class DomainError(Exception):
    """Base exception for domain rule violations.

    Args:
        `message` (str):
            - Human-readable error description.
        `code` (str | None):
            - Stable machine-readable error identifier.
    """

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message


# =========================
# User Errors
# =========================


class UserErrorCode(StrEnum):
    """Enumerates user-related domain error codes.

    Attributes:
        `EMAIL_ALREADY_VERIFIED` (str):
            - Raised when the user email has already been verified.
        `INACTIVE_USER` (str):
            - Raised when the user account state is inactive.
        `UNVERIFIED_EMAIL` (str):
            - Raised when an action requires a verified email.
        `MISSING_NEW_EMAIL` (str):
            - Raised when a new email address is required but missing.
    """

    EMAIL_ALREADY_VERIFIED = auto()
    INACTIVE_USER = auto()
    UNVERIFIED_EMAIL = auto()
    MISSING_NEW_EMAIL = auto()


class InactiveUserError(DomainError):
    """Raised when an operation requires an active user.

    Args:
        `message` (str):
            - Human-readable error description.
    """

    def __init__(self, message: str = 'User account is inactive'):
        super().__init__(message, UserErrorCode.INACTIVE_USER)


class EmailAlreadyVerifiedError(DomainError):
    """Raised when email is already verified.

    Args:
        `message` (str):
            - Human-readable error description.
    """

    def __init__(self, message: str = 'Email is already verified'):
        super().__init__(message, UserErrorCode.EMAIL_ALREADY_VERIFIED)


class UnverifiedEmailError(DomainError):
    """Raised when an operation requires a verified email.

    Args:
        `message` (str):
            - Human-readable error description.
    """

    def __init__(self, message: str = 'Email address is not verified'):
        super().__init__(message, UserErrorCode.UNVERIFIED_EMAIL)


# =========================
# Password Validation Errors
# =========================


class PasswordErrorCode(StrEnum):
    """Enumerates password validation error codes.

    Attributes:
        `PASSWORD_REQUIRED` (str):
            - Indicates that the password field is missing or empty.
        `PASSWORD_TOO_SHORT` (str):
            - Raised when the password does not meet the minimum length
              requirement.
        `PASSWORD_TOO_LONG` (str):
            - Raised when the password exceeds the maximum allowed length.
        `PASSWORD_MISSING_LETTER` (str):
            - Indicates the password lacks at least one alphabetic
              character.
        `PASSWORD_MISSING_NUMBER` (str):
            - Indicates the password lacks at least one numeric digit.
        `PASSWORD_MISSING_SPECIAL` (str):
            - Indicates the password lacks at least one special character.
        `PASSWORD_MISSING_UPPERCASE` (str):
            - Indicates the password lacks at least one uppercase letter.
        `PASSWORD_MISSING_LOWERCASE` (str):
            - Indicates the password lacks at least one lowercase letter.
    """

    PASSWORD_REQUIRED = auto()
    PASSWORD_TOO_SHORT = auto()
    PASSWORD_TOO_LONG = auto()
    PASSWORD_MISSING_LETTER = auto()
    PASSWORD_MISSING_NUMBER = auto()
    PASSWORD_MISSING_SPECIAL = auto()
    PASSWORD_MISSING_UPPERCASE = auto()
    PASSWORD_MISSING_LOWERCASE = auto()


class InvalidPasswordError(DomainError):
    """Use with a specific PasswordErrorCode.

    Args:
        `message` (str):
            - Human-readable error description.
        `code` (PasswordErrorCode):
            - Password validation failure type.
    """

    def __init__(self, message: str, code: PasswordErrorCode):
        super().__init__(message, code)


# =========================
# Email Validation Errors
# =========================


class EmailErrorCode(StrEnum):
    """Enumerates email validation error codes.

    Attributes:
        `EMAIL_REQUIRED` (str):
            - Indicates that the email field is missing or empty.
        `EMAIL_INVALID_FORMAT` (str):
            - Raised when the provided email string format is invalid.
    """

    EMAIL_REQUIRED = auto()
    EMAIL_INVALID_FORMAT = auto()


class InvalidEmailError(DomainError):
    """Use with a specific EmailErrorCode.

    Args:
        `message` (str):
            - Human-readable error description.
        `code` (EmailErrorCode):
            - Email validation failure type.
    """

    def __init__(self, message: str, code: EmailErrorCode):
        super().__init__(message, code)


# =========================
# Code Validation Errors (Input level)
# =========================


class CodeErrorCode(StrEnum):
    """Enumerates code validation error codes.

    Attributes:
        `CODE_INVALID_FORMAT` (str):
            - Raised when the code structure or format
              is invalid.
    """

    CODE_INVALID_FORMAT = auto()


class InvalidCodeError(DomainError):
    """Use for malformed codes.

    Args:
        `message` (str):
            - Human-readable error description.
        `code` (CodeErrorCode):
            - Code failure type.
    """

    def __init__(self, message: str, code: CodeErrorCode):
        super().__init__(message, code)


# =========================
# Verification Code Domain Errors
# =========================


class VerificationCodeErrorCode(StrEnum):
    """Enumerates verification code domain error codes.

    Attributes:
        `VERIFICATION_CODE_EXPIRED` (str):
            - Raised when the verification code validity has expired.
        `VERIFICATION_CODE_ALREADY_USED` (str):
            - Raised when the verification code has already been consumed.
        `VERIFICATION_CODE_INCORRECT_TYPE` (str):
            - Raised when the verification code purpose type is invalid.
    """

    VERIFICATION_CODE_EXPIRED = auto()
    VERIFICATION_CODE_ALREADY_USED = auto()
    VERIFICATION_CODE_INCORRECT_TYPE = auto()


class VerificationCodeAlreadyUsedError(DomainError):
    """Raised when verification code has already been used.

    Args:
        `message` (str):
            - Human-readable error description.
    """

    def __init__(
        self, message: str = 'Verification code has already been used'
    ):
        super().__init__(
            message, VerificationCodeErrorCode.VERIFICATION_CODE_ALREADY_USED
        )


class VerificationCodeTypeError(DomainError):
    """Raised when verification code type is incorrect.

    Args:
        `message` (str):
            - Human-readable error description.
    """

    def __init__(self, message: str = 'Verification code type is incorrect'):
        super().__init__(
            message, VerificationCodeErrorCode.VERIFICATION_CODE_INCORRECT_TYPE
        )


class VerificationCodeExpiredError(DomainError):
    """Raised when verification code has expired.

    Args:
        `message` (str):
            - Human-readable error description.
    """

    def __init__(self, message: str = 'Verification code has expired'):
        super().__init__(
            message, VerificationCodeErrorCode.VERIFICATION_CODE_EXPIRED
        )


class MissingNewEmailError(DomainError):
    """Raised when new_email is required but missing in payload.

    Args:
        `message` (str):
            - Human-readable error description.
    """

    def __init__(
        self,
        message: str = 'CHANGE_EMAIL codes require "new_email" in payload',
    ):
        super().__init__(message, UserErrorCode.MISSING_NEW_EMAIL)
