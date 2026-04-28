from enum import StrEnum


class DomainError(Exception):
    """Base exception for domain rule violations.

    Args:
        message (str): Human-readable error description.
        code (str | None): Stable machine-readable error identifier.
    """

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.code = code


class PasswordErrorCode(StrEnum):
    REQUIRED = 'PASSWORD_REQUIRED'
    TOO_SHORT = 'PASSWORD_TOO_SHORT'
    TOO_LONG = 'PASSWORD_TOO_LONG'
    MISSING_LETTER = 'PASSWORD_MISSING_LETTER'
    MISSING_NUMBER = 'PASSWORD_MISSING_NUMBER'
    MISSING_SPECIAL = 'PASSWORD_MISSING_SPECIAL'
    MISSING_UPPERCASE = 'PASSWORD_MISSING_UPPERCASE'
    MISSING_LOWERCASE = 'PASSWORD_MISSING_LOWERCASE'


class EmailErrorCode(StrEnum):
    REQUIRED = 'EMAIL_REQUIRED'
    INVALID_FORMAT = 'EMAIL_INVALID_FORMAT'


class CodeErrorCode(StrEnum):
    INVALID_FORMAT = 'CODE_INVALID_FORMAT'


class VerificationCodeErrorCode(StrEnum):
    EXPIRED = 'CODE_EXPIRED'


class InvalidPasswordError(DomainError):
    """Raised when password violates domain rules.

    Args:
        message (str): Human-readable error description.
        code (PasswordErrorCode): Specific password validation failure.
    """

    def __init__(self, message: str, code: PasswordErrorCode):
        super().__init__(message, code)


class InvalidEmailError(DomainError):
    """Raised when email violates domain rules.

    Args:
        message (str): Human-readable error description.
        code (EmailErrorCode): Specific email validation failure.
    """

    def __init__(self, message: str, code: EmailErrorCode):
        super().__init__(message, code)


class InvalidCodeError(DomainError):
    """Raised when verification code is invalid.

    Args:
        message (str): Human-readable error description.
        code (CodeErrorCode): Specific code validation failure.
    """

    def __init__(self, message: str, code: CodeErrorCode):
        super().__init__(message, code)


class VerificationCodeExpiredError(DomainError):
    """Raised when verification code has expired.

    Args:
        message (str): Human-readable expiration error description.
    """

    def __init__(self, message: str = 'Code has expired'):
        super().__init__(message, VerificationCodeErrorCode.EXPIRED)
