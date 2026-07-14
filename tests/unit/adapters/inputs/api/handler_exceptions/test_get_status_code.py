import pytest

import application.exceptions as application_exceptions
import domain.exceptions as domain_exceptions
from adapters.inputs.api.handler_exceptions import get_status_code

cases = [
    (application_exceptions.PasswordMismatchError(), 400),
    (application_exceptions.InvalidTokenTypeError(), 400),
    (
        application_exceptions.InvalidTokenError(
            application_exceptions.InvalidTokenErrorCode.TOKEN_EXPIRED
        ),
        401,
    ),
    (application_exceptions.InvalidCredentialsError(), 401),
    (application_exceptions.TokenRevokedError(), 401),
    (application_exceptions.UserNotFoundError(), 404),
    (application_exceptions.VerificationCodeNotFoundError(), 404),
    (application_exceptions.TokenNotFoundError(), 404),
    (application_exceptions.EmailAlreadyUsedError(), 409),
    (
        domain_exceptions.InvalidPasswordError(
            '',
            domain_exceptions.PasswordErrorCode.PASSWORD_MISSING_LETTER,
        ),
        400,
    ),
    (
        domain_exceptions.InvalidEmailError(
            '',
            domain_exceptions.EmailErrorCode.EMAIL_REQUIRED,
        ),
        400,
    ),
    (
        domain_exceptions.InvalidCodeError(
            '',
            domain_exceptions.CodeErrorCode.CODE_INVALID_FORMAT,
        ),
        400,
    ),
    (domain_exceptions.VerificationCodeTypeError(), 400),
    (domain_exceptions.MissingNewEmailError(), 400),
    (domain_exceptions.InactiveUserError(), 403),
    (domain_exceptions.UnverifiedEmailError(), 403),
    (domain_exceptions.EmailAlreadyVerifiedError(), 409),
    (domain_exceptions.VerificationCodeAlreadyUsedError(), 409),
    (domain_exceptions.VerificationCodeExpiredError(), 410),
    (Exception(), 500),
]


@pytest.mark.parametrize(('exc', 'expected_status_code'), cases)
def test_return_status_code_correctly(exc, expected_status_code):
    actual_status_code = get_status_code(exc)
    assert actual_status_code == expected_status_code
