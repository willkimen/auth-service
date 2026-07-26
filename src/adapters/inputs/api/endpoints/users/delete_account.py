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
    header_authorization: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    use_case: DeleteAccountCodeDep,
    settings: SettingsDep,
):
    """
    Starts the account deletion process for the authenticated user by
    generating a verification code and sending it to the user's
    registered email address.

    Args:
        `header_authorization` (`HTTPAuthorizationCredentials`):
            - HTTP Bearer credentials containing the access token used
              to authenticate the user.

        `use_case` (`DeleteAccountCodeDep`):
            - Dependency responsible for executing the account deletion
              verification code generation workflow.

        `settings` (`SettingsDep`):
            - Application settings containing the verification code
              expiration time.

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
        header_authorization.credentials,
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
    Completes the account deletion process for the authenticated user
    by validating the verification code and deleting the account.

    Args:
        `body` (`VerificationCodeRequest`):
            - Request body containing the account deletion verification
              code.

        `credentials` (`HTTPAuthorizationCredentials`):
            - HTTP Bearer credentials containing the access token used
              to authenticate the user.

        `use_case` (`DeleteAccountDep`):
            - Dependency responsible for executing the authenticated
              account deletion workflow.

        `settings` (`SettingsDep`):
            - Application settings used by the account deletion workflow.

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
