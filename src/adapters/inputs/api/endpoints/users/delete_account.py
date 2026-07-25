from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adapters.inputs.api.dependencies.adapters import SettingsDep
from adapters.inputs.api.dependencies.use_cases import (
    DeleteAccountCodeDep,
    DeleteAccountDep,
)
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import VerificationCodeRequest

bearer_scheme = HTTPBearer()


@users_router.post(
    '/delete/code',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_account_code(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    use_case: DeleteAccountCodeDep,
    settings: SettingsDep,
):
    """
    Generates and persists a verification code used to authorize
    the account deletion process for an authenticated user.

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
    '/delete',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_account(
    body: VerificationCodeRequest,
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    use_case: DeleteAccountDep,
    settings: SettingsDep,
):
    """
    Handles the authenticated account deletion workflow.

    Args:
        `body` (`VerificationCodeRequest`):
            - Verification code sent to the new email address.

    Raises:
        `InvalidTokenError`:
            - If token validation fails at domain level.
        `InvalidTokenTypeError`:
            - If token type is not an access token.
        `InfrastructureError`:
            - If token decoding, persistence, or transactional
              operations fail unexpectedly.
        `UserNotFoundError`:
            - If authenticated user cannot be found.
        `InactiveUserError`:
            - If authenticated user is inactive.
        `VerificationCodeNotFoundError`:
            - If verification code does not exist.
        `VerificationCodeAlreadyUsedError`:
            - If verification code was already consumed.
        `VerificationCodeTypeError`:
            - If verification code is not DELETE_ACCOUNT type.
        `VerificationCodeExpiredError`:
            - If verification code has expired.
    """
    await use_case.execute(
        credentials.credentials,
        body.code,
    )
