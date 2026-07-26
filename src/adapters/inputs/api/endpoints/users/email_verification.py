from fastapi import status

from adapters.inputs.api.dependencies.adapters import SettingsDep
from adapters.inputs.api.dependencies.use_cases import (
    EmailVerificationCodeDep,
    EmailVerificationDep,
)
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import (
    EmailAndCodeBodyRequest,
    EmailBodyRequest,
)


@users_router.post(
    '/email/verify/code',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def email_verification_code(
    body: EmailBodyRequest,
    use_case: EmailVerificationCodeDep,
    settings: SettingsDep,
):
    """
    Starts the email verification process for a user account.

    This endpoint receives the user's email address and initiates the
    verification process by requesting a verification code that will be
    sent to the provided email address.

    Args:
        `body` (`EmailBodyRequest`):
            - Request body containing the email address associated with
              the account that should be verified.
        `use_case` (`EmailVerificationCodeDep`):
            - Application use case responsible for handling the email
              verification code generation workflow.
        `settings` (`SettingsDep`):
            - Application settings containing the verification code
              expiration time.

    Raises:
        `UserNotFoundError`:
            - If no user exists with the provided email.
        `EmailAlreadyVerifiedError`:
            - If user's email is already verified.
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
    '/email/verify',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def email_verification(
    body: EmailAndCodeBodyRequest,
    use_case: EmailVerificationDep,
):
    """
    Completes the user email verification process.

    This endpoint receives the user's email address and the verification
    code previously sent to that address, allowing the application to
    validate the code and complete the email verification process.

    Args:
        `body` (`EmailAndCodeBodyRequest`):
            - Request body containing the email address associated with
              the account and the verification code previously sent to
              that email address.
        `use_case` (`EmailVerificationDep`):
            - Application use case responsible for validating the
              verification code and completing the email verification
              process.

    Raises:
        `UserNotFoundError`:
            - If no user exists with the provided email.
        `VerificationCodeNotFoundError`:
            - If verification code does not exist for the user and code.
        `EmailAlreadyVerifiedError`:
            - If user's email is already verified.
        `InactiveUserError`:
            - If user account is inactive.
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
            - If an unexpected failure occurs within an output adapter
              (infrastructure layer)
    """
    await use_case.execute(body.email, body.code)
