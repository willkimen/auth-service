from fastapi import status

from auth_service.adapters.inputs.api.dependencies.adapters import SettingsDep
from auth_service.adapters.inputs.api.dependencies.use_cases import (
    ResetPasswordCodeDep,
    ResetPasswordDep,
)
from auth_service.adapters.inputs.api.docs.user_error_responses import (
    reset_password_code_responses,
    reset_password_responses,
)
from auth_service.adapters.inputs.api.routers import users_router
from auth_service.adapters.inputs.api.schemas import (
    EmailBodyRequest,
    ResetPasswordBodyRequest,
)


@users_router.post(
    '/password/reset/code',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Generate password resert verification code',
    description="""
        Starts the password reset process for a user account.
    """,
    responses=reset_password_code_responses,
)
async def reset_password_code(
    body: EmailBodyRequest,
    use_case: ResetPasswordCodeDep,
    settings: SettingsDep,
):
    """
    Starts the password reset process for a user account.

    This endpoint receives the user's email address and initiates the
    password reset process by requesting a verification code that will
    be sent to the provided email address.

    Args:
        `body` (`EmailBodyRequest`):
            - Request body containing the email address associated with
              the account for which the password reset should be initiated.
        `use_case` (`ResetPasswordCodeDep`):
            - Application use case responsible for handling the password
              reset verification code generation workflow.
        `settings` (`SettingsDep`):
            - Application settings containing the verification code
              expiration time.

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
    summary='Reset password',
    description="""
        Completes the password reset process for a user account.
    """,
    responses=reset_password_responses,
)
async def reset_password(
    body: ResetPasswordBodyRequest,
    use_case: ResetPasswordDep,
):
    """
    Completes the password reset process for a user account.

    This endpoint receives the user's email address, the verification
    code previously sent to that address, and the new password. The
    provided information is validated to authorize the password reset
    and complete the process.

    Args:
        `body` (`ResetPasswordBodyRequest`):
            - Request body containing the user's email address,
              password reset verification code, new password, and
              password confirmation.
        `use_case` (`ResetPasswordDep`):
            - Application use case responsible for validating the
              password reset request and completing the password reset
              process.

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
