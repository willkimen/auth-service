from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from adapters.inputs.api.dependencies.use_cases import (
    DetailUserDep,
)
from adapters.inputs.api.routers import users_router
from adapters.inputs.api.schemas import UserPublic
from application.dtos.user_dto import UserPublicDTO

bearer_scheme = HTTPBearer()


@users_router.get(
    '/detail',
    status_code=status.HTTP_200_OK,
    response_model=UserPublic,
)
async def detail(
    credentials: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    use_case: DetailUserDep,
) -> UserPublic:
    """
    Retrieves authenticated user details from a valid access token.

    Returns:
        `UserPublicDTO`:
            - Public-safe representation of the authenticated user.

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
    user: UserPublicDTO = await use_case.execute(credentials.credentials)

    return UserPublic(
        public_id=user.public_id,
        email=user.email,
        email_verified=user.email_verified,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
