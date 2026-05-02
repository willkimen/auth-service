from enum import StrEnum


class DomainError(Exception):
    """Base exception for domain rule violations."""

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


# =========================
# User Errors
# =========================

class UserErrorCode(StrEnum):
    """Enumerates user-related domain error codes."""

    ALREADY_VERIFIED = 'EMAIL_ALREADY_VERIFIED'
    INACTIVE = 'INACTIVE_USER'
    UNVERIFIED_EMAIL = 'UNVERIFIED_EMAIL'
    MISSING_NEW_EMAIL = 'MISSING_NEW_EMAIL'


class InactiveUserError(DomainError):
    """Raised when an operation requires an active user."""

    def __init__(self, message: str = 'User account is inactive'):
        super().__init__(message, UserErrorCode.INACTIVE)


class EmailAlreadyVerifiedError(DomainError):
    """Raised when email is already verified."""

    def __init__(self, message: str = 'Email is already verified'):
        super().__init__(message, UserErrorCode.ALREADY_VERIFIED)


class UnverifiedEmailError(DomainError):
    """Raised when an operation requires a verified email."""

    def __init__(self, message: str = 'Email address is not verified'):
        super().__init__(message, UserErrorCode.UNVERIFIED_EMAIL)


# =========================
# Password Validation Errors
# =========================

class PasswordErrorCode(StrEnum):
    """Enumerates password validation error codes."""

    REQUIRED = 'PASSWORD_REQUIRED'
    TOO_SHORT = 'PASSWORD_TOO_SHORT'
    TOO_LONG = 'PASSWORD_TOO_LONG'
    MISSING_LETTER = 'PASSWORD_MISSING_LETTER'
    MISSING_NUMBER = 'PASSWORD_MISSING_NUMBER'
    MISSING_SPECIAL = 'PASSWORD_MISSING_SPECIAL'
    MISSING_UPPERCASE = 'PASSWORD_MISSING_UPPERCASE'
    MISSING_LOWERCASE = 'PASSWORD_MISSING_LOWERCASE'


class InvalidPasswordError(DomainError):
    """Use with a specific PasswordErrorCode."""

    def __init__(self, message: str, code: PasswordErrorCode):
        super().__init__(message, code)


# =========================
# Email Validation Errors
# =========================

class EmailErrorCode(StrEnum):
    """Enumerates email validation error codes."""

    REQUIRED = 'EMAIL_REQUIRED'
    INVALID_FORMAT = 'EMAIL_INVALID_FORMAT'


class InvalidEmailError(DomainError):
    """Use with a specific EmailErrorCode."""

    def __init__(self, message: str, code: EmailErrorCode):
        super().__init__(message, code)


# =========================
# Code Validation Errors (Input level)
# =========================

class CodeErrorCode(StrEnum):
    """Enumerates verification code validation error codes."""

    INVALID_FORMAT = 'CODE_INVALID_FORMAT'


class InvalidCodeError(DomainError):
    """Use for malformed verification codes."""

    def __init__(self, message: str, code: CodeErrorCode):
        super().__init__(message, code)


# =========================
# Verification Code Domain Errors
# =========================

class VerificationCodeErrorCode(StrEnum):
    """Enumerates verification code domain error codes."""

    EXPIRED = 'VERIFICATION_CODE_EXPIRED'
    ALREADY_USED = 'VERIFICATION_CODE_ALREADY_USED'
    INCORRECT_TYPE = 'VERIFICATION_CODE_INCORRECT_TYPE'


class VerificationCodeAlreadyUsedError(DomainError):
    """Raised when verification code has already been used."""

    def __init__(
            self,
            message: str = 'Verification code has already been used'
    ):
        super().__init__(message, VerificationCodeErrorCode.ALREADY_USED)


class VerificationCodeTypeError(DomainError):
    """Raised when verification code type is incorrect."""

    def __init__(self, message: str = 'Verification code type is incorrect'):
        super().__init__(message, VerificationCodeErrorCode.INCORRECT_TYPE)


class VerificationCodeExpiredError(DomainError):
    """Raised when verification code has expired."""

    def __init__(self, message: str = 'Verification code has expired'):
        super().__init__(message, VerificationCodeErrorCode.EXPIRED)


class MissingNewEmailError(DomainError):
    """Raised when new_email is required but missing in payload."""

    def __init__(
            self,
            message: str = "CHANGE_EMAIL codes require 'new_email' in payload"
    ):
        super().__init__(message, UserErrorCode.MISSING_NEW_EMAIL)
