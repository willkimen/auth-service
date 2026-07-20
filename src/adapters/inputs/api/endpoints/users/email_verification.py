from fastapi import status

from adapters.inputs.api.dependencies.adapters import SettingsDep
from adapters.inputs.api.dependencies.use_cases import (
    EmailVerificationCodeDep,
    EmailVerificationDep,
)
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import EmailAndCodeRequest, EmailRequest


@users_router.post(
    '/email/verify/code',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def email_verification_code(
    body: EmailRequest,
    use_case: EmailVerificationCodeDep,
    settings: SettingsDep,
):
    """
    Starts the email verification process for a user account.

    Args:
        `body` (`EmailRequest`):
            - Request body containing the email address associated with
              the account that should be verified.

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
    body: EmailAndCodeRequest,
    use_case: EmailVerificationDep,
):
    """
    Completes the user email verification process.

    Args:
        `body` (`EmailAndCodeRequest`):
            - Request body containing the email address associated
              with the account and the verification code previously
              sent to that email address.

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
