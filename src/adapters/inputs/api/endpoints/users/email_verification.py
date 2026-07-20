from fastapi import status

from adapters.inputs.api.dependencies.adapters import SettingsDep
from adapters.inputs.api.dependencies.use_cases import (
    EmailVerificationCodeDep,
)
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import EmailRequest


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
