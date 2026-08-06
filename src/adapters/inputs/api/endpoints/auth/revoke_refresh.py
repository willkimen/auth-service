from fastapi import status

from adapters.inputs.api.dependencies.use_cases import (
    RevokeRefreshDep,
)
from adapters.inputs.api.routers import auth_router
from adapters.inputs.api.schemas import RefreshBodyRequest


@auth_router.post(
    '/token/revoke-refresh',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Revoke refresh token',
    description="""
        Revokes a specific refresh token, invalidating the authenticated
        session associated with that token.
    """,
)
async def revoke_refresh(
    body: RefreshBodyRequest,
    use_case: RevokeRefreshDep,
):
    """
    Revokes a specific refresh token, invalidating the authenticated
    session associated with that token.

    Args:
        `body` (`RefreshBodyRequest`):
            - Request body containing the refresh token to be revoked.
        `use_case` (`RevokeRefreshDep`):
            - Injected application use case responsible for validating
              and revoking the specified refresh token.

    Raises:
        `InfrastructureError`:
            - If token validation or persistence operations fail.
        `InvalidTokenError`:
            - If token validation fails.
        `InvalidTokenTypeError`:
            - If token type is not a refresh token.
    """
    await use_case.execute(body.refresh)
