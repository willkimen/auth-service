from auth_service.adapters.inputs.api.docs.helpers import error_example
from auth_service.application.exceptions import (
    EmailAlreadyUsedError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidTokenErrorCode,
    InvalidTokenTypeError,
    PasswordMismatchError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)

EMAIL_ALREADY_USED_EXAMPLES = {
    'email_already_used': error_example(
        'Email already used',
        EmailAlreadyUsedError(),
    ),
}


USER_NOT_FOUND_EXAMPLES = {
    'user_not_found': error_example(
        'User not found',
        UserNotFoundError(),
    ),
}


VERIFICATION_CODE_NOT_FOUND_EXAMPLES = {
    'verification_code_not_found': error_example(
        'Verification code not found',
        VerificationCodeNotFoundError(),
    ),
}


PASSWORD_MISMATCH_EXAMPLES = {
    'password_mismatch': error_example(
        'Password mismatch',
        PasswordMismatchError(),
    ),
}


INVALID_CREDENTIALS_EXAMPLES = {
    'invalid_credentials': error_example(
        'Invalid credentials',
        InvalidCredentialsError(),
    ),
}


INVALID_TOKEN_EXAMPLES = {
    'token_expired': error_example(
        'Token expired',
        InvalidTokenError(
            InvalidTokenErrorCode.TOKEN_EXPIRED,
        ),
    ),
    'token_invalid_signature': error_example(
        'Token invalid signature',
        InvalidTokenError(
            InvalidTokenErrorCode.TOKEN_INVALID_SIGNATURE,
        ),
    ),
    'token_malformed': error_example(
        'Token malformed',
        InvalidTokenError(
            InvalidTokenErrorCode.TOKEN_MALFORMED,
        ),
    ),
    'token_invalid': error_example(
        'Token invalid',
        InvalidTokenError(
            InvalidTokenErrorCode.TOKEN_INVALID,
        ),
    ),
}


TOKEN_NOT_FOUND_EXAMPLES = {
    'token_not_found': error_example(
        'Token not found',
        TokenNotFoundError(),
    ),
}


TOKEN_REVOKED_EXAMPLES = {
    'token_revoked': error_example(
        'Token revoked',
        TokenRevokedError(),
    ),
}


INVALID_TOKEN_TYPE_EXAMPLES = {
    'invalid_token_type': error_example(
        'Invalid token type',
        InvalidTokenTypeError(),
    ),
}
