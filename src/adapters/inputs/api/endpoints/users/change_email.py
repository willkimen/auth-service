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
    ChangeEmailCodeBodyRequest,
    VerificationCodeBodyRequest,
)

bearer_scheme = HTTPBearer()


@users_router.post(
    '/email/change/code',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Generate email change verification code',
    description="""
        Starts the email change process for the authenticated user by
        generating a verification code and sending it to the requested
        new email address.
    """,
)
async def change_email_code(
    header_authorization: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    body: ChangeEmailCodeBodyRequest,
    use_case: ChangeEmailCodeDep,
    settings: SettingsDep,
):
    """
    Starts the email change process for the authenticated user by
    generating a verification code and sending it to the requested
    new email address.

    Args:
        `header_authorization` (`HTTPAuthorizationCredentials`):
            - HTTP Bearer credentials containing the access token used
              to authenticate the user.

        `body` (`ChangeEmailCodeBodyRequest`):
            - Request body containing the new email address that will
              receive the email change verification code.

        `use_case` (`ChangeEmailCodeDep`):
            - Dependency responsible for executing the email change
              verification code generation workflow.

        `settings` (`SettingsDep`):
            - Application settings containing the verification code
              expiration time.

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
        header_authorization.credentials,
        body.new_email,
        settings.code_expiration_time,
    )


@users_router.post(
    '/email/change',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Change user email',
    description="""
        Completes the email change process for the authenticated user by
        validating the verification code sent to the requested new email
        address and applying the email change.
    """,
)
async def change_email(
    header_authorization: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    body: VerificationCodeBodyRequest,
    use_case: ChangeEmailDep,
):
    """
    Completes the email change process for the authenticated user by
    validating the verification code sent to the requested new email
    address and applying the email change.

    Args:
        `header_authorization` (`HTTPAuthorizationCredentials`):
            - HTTP Bearer credentials containing the access token used
              to authenticate the user.

        `body` (`VerificationCodeBodyRequest`):
            - Request body containing the verification code sent to the
              user's new email address.

        `use_case` (`ChangeEmailDep`):
            - Dependency responsible for executing the email change
              verification workflow.

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
        header_authorization.credentials,
        body.code,
    )
