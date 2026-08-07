from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adapters.inputs.api.dependencies.use_cases import (
    DetailUserDep,
)
from adapters.inputs.api.docs.user_error_responses import detail_responses
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import UserPublicBodyResponse
from application.dtos.user_dto import UserPublicDTO

bearer_scheme = HTTPBearer()


@users_router.get(
    '/detail',
    status_code=status.HTTP_200_OK,
    response_model=UserPublicBodyResponse,
    summary='Get authenticated user details',
    description="""
        Retrieves the authenticated user's public account information using
        a valid access token.
    """,
    responses=detail_responses,
)
async def detail(
    header_authorization: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    use_case: DetailUserDep,
) -> UserPublicBodyResponse:
    """
    Retrieves the authenticated user's public account information using
    a valid access token.

    Args:
        `header_authorization` (`HTTPAuthorizationCredentials`):
            - HTTP Bearer credentials containing the access token used
              to authenticate the user.

        `use_case` (`DetailUserDep`):
            - Dependency responsible for retrieving the authenticated
              user's details.

    Returns:
        `UserPublicBodyResponse`:
            - Public representation of the authenticated user's account
              information.

    Raises:
        `InvalidTokenError`:
            - Raised when token validation fails.
        `InvalidTokenTypeError`:
            - If token type is not an access token.
        `UserNotFoundError`:
            - If no user exists for the token subject.
        `InactiveUserError`:
            - If user account is inactive.
        `CorruptedPersistenceStateError`:
            - Raised when persisted data cannot be reconstructed
              into valid domain objects.
        `InfrastructureError`:
            - If an unexpected failure occurs within an output
              adapter (infrastructure layer).

    """
    user: UserPublicDTO = await use_case.execute(
        header_authorization.credentials
    )

    return UserPublicBodyResponse(
        public_id=user.public_id,
        email=user.email,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
