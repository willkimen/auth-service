from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adapters.inputs.api.dependencies.adapters import SettingsDep
from adapters.inputs.api.dependencies.use_cases import (
    ChangePasswordCodeDep,
    ChangePasswordDep,
)
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import ChangePasswordRequest

bearer_scheme = HTTPBearer()


@users_router.post(
    '/password/change/code',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_password_code(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    use_case: ChangePasswordCodeDep,
    settings: SettingsDep,
):
    """
    Generates and persists a verification code used to authorize a
    password change operation for an authenticated user.

    Raises:
        `InvalidTokenError`:
            - Raised when the provided token is invalid, expired,
              malformed, or contains invalid claims.
        `InvalidTokenTypeError`:
            - If token type is not an access token.
        `UserNotFoundError`:
            - Raised when the authenticated user no longer exists.
        `InactiveUserError`:
            - Raised when the authenticated user is inactive.
        `CorruptedPersistenceStateError`:
            - Raised when persisted user data cannot be reconstructed
              into valid domain objects.
        `InfrastructureError`:
            - Raised when persistence operations, token operations,
              transaction handling, or external infrastructure services
              fail unexpectedly.
    """
    await use_case.execute(
        credentials.credentials,
        settings.code_expiration_time,
    )


@users_router.post(
    '/password/change',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_password(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    body: ChangePasswordRequest,
    use_case: ChangePasswordDep,
):
    """
    Handles the authenticated password change workflow.

    Args:
        `body` (`ChangePasswordRequest`):
            - Request body containing password change verification code,
              new password, and password confirmation.

    Raises:
        `InvalidPasswordError`:
            - If password policy validation fails.
        `PasswordMismatchError`:
            - If password confirmation does not match.
        `InfrastructureError`:
            - If hashing, repositories, transactions,
              or persistence operations fail.
        `InvalidTokenError`:
            - If token validation fails.
        `InvalidTokenTypeError`:
            - If token type is not an access token.
        `UserNotFoundError`:
            - If authenticated user cannot be found.
        `InactiveUserError`:
            - If authenticated user is inactive.
        `VerificationCodeNotFoundError`:
            - If verification code does not exist.
        `VerificationCodeAlreadyUsedError`:
            - If verification code was already consumed.
        `VerificationCodeTypeError`:
            - If verification code type is invalid.
        `VerificationCodeExpiredError`:
            - If verification code has expired.
    """
    await use_case.execute(
        credentials.credentials,
        body.code,
        body.new_password,
        body.new_password_confirmation,
    )
