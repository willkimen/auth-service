from fastapi import status

from adapters.inputs.api.dependencies.use_cases import (
    RevokeAllRefreshesDep,
)
from adapters.inputs.api.routers import auth_router
from adapters.inputs.api.schemas import (
    RefreshBodyRequest,
)


@auth_router.post(
    '/token/revoke-all-refreshes',
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_all_refreshes(
    body: RefreshBodyRequest,
    use_case: RevokeAllRefreshesDep,
):
    """
    Revokes all refresh tokens associated with the authenticated user,
    invalidating all active refresh-token sessions.

    Args:
        `body` (`RefreshBodyRequest`):
            - Request body containing the refresh token used to identify
              the authenticated user whose refresh tokens should be revoked.

    Raises:
        `InfrastructureError`:
            - If token validation or persistence operations fail.
        `InvalidTokenError`:
            - If token validation fails.
        `InvalidTokenTypeError`:
            - If token type is not a refresh token.
    """
    await use_case.execute(body.refresh)
