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
    header_authorization: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    use_case: ChangePasswordCodeDep,
    settings: SettingsDep,
):
    """
    Starts the password change process for the authenticated user by
    generating a verification code and sending it to the user's
    registered email address.

    Args:
        `header_authorization` (`HTTPAuthorizationCredentials`):
            - HTTP Bearer credentials containing the access token used
              to authenticate the user.

        `use_case` (`ChangePasswordCodeDep`):
            - Dependency responsible for executing the password change
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
    '/password/change',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def change_password(
    header_authorization: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    body: ChangePasswordRequest,
    use_case: ChangePasswordDep,
):
    """
    Completes the password change process for the authenticated user
    by validating the verification code and applying the new password.

    Args:
        `header_authorization` (`HTTPAuthorizationCredentials`):
            - HTTP Bearer credentials containing the access token used
              to authenticate the user.

        `body` (`ChangePasswordRequest`):
            - Request body containing the password change verification
              code, new password, and password confirmation.

        `use_case` (`ChangePasswordDep`):
            - Dependency responsible for executing the authenticated
              password change workflow.

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
        header_authorization.credentials,
        body.code,
        body.new_password,
        body.new_password_confirmation,
    )
