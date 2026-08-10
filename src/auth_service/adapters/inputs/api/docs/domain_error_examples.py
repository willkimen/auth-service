from auth_service.adapters.inputs.api.docs.helpers import error_example
from auth_service.domain.exceptions import (
    CodeErrorCode,
    EmailAlreadyVerifiedError,
    EmailErrorCode,
    InactiveUserError,
    InvalidCodeError,
    InvalidEmailError,
    InvalidPasswordError,
    MissingNewEmailError,
    PasswordErrorCode,
    UnverifiedEmailError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)

INACTIVE_USER_EXAMPLES = {
    'inactive_user': error_example(
        'Inactive user',
        InactiveUserError(),
    ),
}


EMAIL_ALREADY_VERIFIED_EXAMPLES = {
    'email_already_verified': error_example(
        'Email already verified',
        EmailAlreadyVerifiedError(),
    ),
}


UNVERIFIED_EMAIL_EXAMPLES = {
    'unverified_email': error_example(
        'Unverified email',
        UnverifiedEmailError(),
    ),
}


INVALID_PASSWORD_EXAMPLES = {
    'password_required': error_example(
        'Password required',
        InvalidPasswordError(
            'Password is required',
            PasswordErrorCode.PASSWORD_REQUIRED,
        ),
    ),
    'password_too_short': error_example(
        'Password too short',
        InvalidPasswordError(
            'Password is too short',
            PasswordErrorCode.PASSWORD_TOO_SHORT,
        ),
    ),
    'password_too_long': error_example(
        'Password too long',
        InvalidPasswordError(
            'Password is too long',
            PasswordErrorCode.PASSWORD_TOO_LONG,
        ),
    ),
    'password_missing_letter': error_example(
        'Password missing letter',
        InvalidPasswordError(
            'Password must contain at least one letter',
            PasswordErrorCode.PASSWORD_MISSING_LETTER,
        ),
    ),
    'password_missing_number': error_example(
        'Password missing number',
        InvalidPasswordError(
            'Password must contain at least one number',
            PasswordErrorCode.PASSWORD_MISSING_NUMBER,
        ),
    ),
    'password_missing_special': error_example(
        'Password missing special character',
        InvalidPasswordError(
            'Password must contain at least one special character',
            PasswordErrorCode.PASSWORD_MISSING_SPECIAL,
        ),
    ),
    'password_missing_uppercase': error_example(
        'Password missing uppercase letter',
        InvalidPasswordError(
            'Password must contain at least one uppercase letter',
            PasswordErrorCode.PASSWORD_MISSING_UPPERCASE,
        ),
    ),
    'password_missing_lowercase': error_example(
        'Password missing lowercase letter',
        InvalidPasswordError(
            'Password must contain at least one lowercase letter',
            PasswordErrorCode.PASSWORD_MISSING_LOWERCASE,
        ),
    ),
}


INVALID_EMAIL_EXAMPLES = {
    'email_required': error_example(
        'Email required',
        InvalidEmailError(
            'Email is required',
            EmailErrorCode.EMAIL_REQUIRED,
        ),
    ),
    'email_invalid_format': error_example(
        'Invalid email format',
        InvalidEmailError(
            'Invalid email format',
            EmailErrorCode.EMAIL_INVALID_FORMAT,
        ),
    ),
}


INVALID_CODE_EXAMPLES = {
    'invalid_code_format': error_example(
        'Invalid code format',
        InvalidCodeError(
            'Invalid code format',
            CodeErrorCode.CODE_INVALID_FORMAT,
        ),
    ),
}


VERIFICATION_CODE_ALREADY_USED_EXAMPLES = {
    'verification_code_already_used': error_example(
        'Verification code already used',
        VerificationCodeAlreadyUsedError(),
    ),
}


VERIFICATION_CODE_TYPE_EXAMPLES = {
    'verification_code_incorrect_type': error_example(
        'Verification code incorrect type',
        VerificationCodeTypeError(),
    ),
}


VERIFICATION_CODE_EXPIRED_EXAMPLES = {
    'verification_code_expired': error_example(
        'Verification code expired',
        VerificationCodeExpiredError(),
    ),
}


MISSING_NEW_EMAIL_EXAMPLES = {
    'missing_new_email': error_example(
        'Missing new email',
        MissingNewEmailError(),
    ),
}
