from fastapi import status

from adapters.inputs.api.dependencies.use_cases import RefreshDep
from adapters.inputs.api.routers import auth_router
from adapters.inputs.api.schemas import (
    AccessBodyResponse,
    RefreshBodyRequest,
)


@auth_router.post(
    '/token/refresh',
    status_code=status.HTTP_200_OK,
    response_model=AccessBodyResponse,
    summary='Refresh access token',
    description="""
        Generates a new access token using a valid refresh token.
    """,
)
async def refresh_token(
    body: RefreshBodyRequest,
    use_case: RefreshDep,
) -> AccessBodyResponse:
    """
    Generates a new access token using a valid refresh token.

    Args:
        `body` (`RefreshBodyRequest`):
            - Request body containing the refresh token used to
              authenticate the token renewal operation.
        `use_case` (`RefreshDep`):
            - Injected application use case responsible for validating
              the refresh token and generating a new access token.

    Returns:
        `AccessBodyResponse`:
            - Response body containing the newly generated access token.

    Raises:
        `InfrastructureError`:
            - If token validation, repositories, or token
              generation operations fail.
        `InvalidTokenError`:
            - If token validation fails.
        `InvalidTokenTypeError`:
            - If token type is not a refresh token.
        `TokenNotFoundError`:
            - If refresh token does not exist.
        `TokenRevokedError`:
            - If refresh token has been revoked.
        `UserNotFoundError`:
            - If authenticated user cannot be found.
        `InactiveUserError`:
            - If authenticated user is inactive.
        `CorruptedPersistenceStateError`:
            - If persisted user state is corrupted.
    """
    access: str = await use_case.execute(body.refresh)

    return AccessBodyResponse(access=access)
