from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth_service.adapters.inputs.api.dependencies.adapters import SettingsDep
from auth_service.adapters.inputs.api.dependencies.use_cases import (
    DeleteAccountCodeDep,
    DeleteAccountDep,
)
from auth_service.adapters.inputs.api.docs.user_error_responses import (
    delete_account_code_responses,
    delete_account_responses,
)
from auth_service.adapters.inputs.api.routers import users_router
from auth_service.adapters.inputs.api.schemas import (
    VerificationCodeBodyRequest,
)

bearer_scheme = HTTPBearer()


@users_router.post(
    '/delete/code',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Generate account delete verification code',
    description="""
        Starts the account deletion process for the authenticated user by
        generating a verification code and sending it to the user's
        registered email address.
        """,
    responses=delete_account_code_responses,
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
    summary='Delete account',
    description="""
        Completes the account deletion process for the authenticated user
        by validating the verification code and deleting the account.
        """,
    responses=delete_account_responses,
)
async def delete_account(
    body: VerificationCodeBodyRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
    use_case: DeleteAccountDep,
    settings: SettingsDep,
):
    """
    Completes the account deletion process for the authenticated user
    by validating the verification code and deleting the account.

    Args:
        `body` (`VerificationCodeBodyRequest`):
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
