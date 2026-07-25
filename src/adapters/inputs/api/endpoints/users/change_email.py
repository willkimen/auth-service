from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adapters.inputs.api.dependencies.adapters import SettingsDep
from adapters.inputs.api.dependencies.use_cases import (
    ChangeEmailCodeDep,
    ChangeEmailDep,
)
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import (
    ChangeEmailCodeRequest,
    VerificationCodeRequest,
)

bearer_scheme = HTTPBearer()


@users_router.post(
    '/email/change/code',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_email_code(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    body: ChangeEmailCodeRequest,
    use_case: ChangeEmailCodeDep,
    settings: SettingsDep,
):
    """
    Initializes the email change verification process for
    an authenticated user.

    Args:
        `body` (`ChangeEmailCodeRequest`):
            - Request body containing the new email address to change email.

    Raises:
        `InvalidEmailError`:
            - Raised when the provided email is invalid.
        `InvalidTokenError`:
            - Raised when token validation fails.
        `InvalidTokenTypeError`:
            - If token type is not an access token.
        `UserNotFoundError`:
            - Raised when no user exists for the authenticated token.
        `InactiveUserError`:
            - Raised when the authenticated user is inactive.
        `CorruptedPersistenceStateError`:
            - Raised when persisted data cannot be reconstructed
              into valid domain objects.
        `InfrastructureError`:
            - Raised when an unexpected infrastructure failure occurs
              within an output adapter.
    """
    await use_case.execute(
        credentials.credentials,
        body.new_email,
        settings.code_expiration_time,
    )


@users_router.post(
    '/email/change',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_email(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    body: VerificationCodeRequest,
    use_case: ChangeEmailDep,
):
    """
    Completes the user email change process using a previously
    generated verification code associated with an authenticated
    session.

    Args:
        `body` (`VerificationCodeRequest`):
            - Verification code sent to the new email address.

    Raises:
        `InvalidTokenError`:
            - If the provided token is malformed, invalid,
              expired, or cannot be decoded.
        `InvalidTokenTypeError`:
            - If token type is not an access token.
        `VerificationCodeNotFoundError`:
            - If no verification code exists for the user and
              provided code.
        `VerificationCodeAlreadyUsedError`:
            - If the verification code was already used.
        `VerificationCodeTypeError`:
            - If the verification code type is invalid for the
              email change operation.
        `VerificationCodeExpiredError`:
            - If the verification code has expired.
        `UserNotFoundError`:
            - If no user exists for the authenticated token.
        `InactiveUserError`:
            - If the user account is inactive.
        `InvalidEmailError`:
            - If the email extracted from the verification code
              is invalid.
        `CorruptedPersistenceStateError`:
            - Raised when persisted data cannot be reconstructed
              into valid domain entities or value objects.
        `InfrastructureError`:
            - If an unexpected failure occurs in the infrastructure
              layer during repository, token, or persistence
              operations.
    """
    await use_case.execute(
        credentials.credentials,
        body.code,
    )
