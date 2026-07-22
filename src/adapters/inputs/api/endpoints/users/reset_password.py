from fastapi import status

from adapters.inputs.api.dependencies.adapters import SettingsDep
from adapters.inputs.api.dependencies.use_cases import (
    ResetPasswordCodeDep,
    ResetPasswordDep,
)
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import EmailRequest, ResetPasswordRequest


@users_router.post(
    '/password/reset/code',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reset_password_code(
    body: EmailRequest,
    use_case: ResetPasswordCodeDep,
    settings: SettingsDep,
):
    """
    Starts the password reset process for a user account.

    Args:
        `body` (`EmailRequest`):
            - Request body containing the email address associated with
              the account.

    Raises:
        `UserNotFoundError`:
            - If no user exists with the provided email.
        `InactiveUserError`:
            - If user account is inactive.
        `CorruptedPersistenceStateError`:
            - Raised when persisted data cannot be reconstructed
              into valid domain objects.
        `InfrastructureError`:
            - If an unexpected failure occurs within an output adapter
              (infrastructure layer)
    """
    await use_case.execute(body.email, settings.code_expiration_time)


@users_router.post(
    '/password/reset',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def reset_password(
    body: ResetPasswordRequest,
    use_case: ResetPasswordDep,
):
    """
    Completes the password reset process for a user account.

    Args:
        `body` (`ResetPasswordRequest`):
            - Request body containing the user's email address,
              password reset verification code, new password, and
              password confirmation.

    Raises:
        `InvalidPasswordError`:
            - Raised when the password does not satisfy the
              password policy.
        `PasswordMismatchError`:
            - Raised when password and confirmation password do
              not match.
        `UserNotFoundError`:
            - If no user exists with the provided email.
        `InactiveUserError`:
            - If user account is inactive.
        `VerificationCodeNotFoundError`:
            - If verification code does not exist for the user
              and code.
        `VerificationCodeAlreadyUsedError`:
            - If verification code was already used.
        `VerificationCodeExpiredError`:
            - If verification code has expired.
        `VerificationCodeTypeError`:
            - If verification code type is incorrect.
        `CorruptedPersistenceStateError`:
            - Raised when persisted data cannot be reconstructed
              into valid domain objects.
        `InfrastructureError`:
            - If an unexpected failure occurs within an output
              adapter (infrastructure layer)

    """
    await use_case.execute(
        body.email,
        body.code,
        body.password,
        body.password_confirmation,
    )
