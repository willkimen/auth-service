from typing import Annotated

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth_service.adapters.inputs.api.dependencies.use_cases import (
    RevokeAllRefreshesDep,
)
from auth_service.adapters.inputs.api.docs.authentication_error_responses import (
    revoke_all_refreshes_responses,
)
from auth_service.adapters.inputs.api.routers import auth_router

bearer_scheme = HTTPBearer()


@auth_router.post(
    '/token/revoke-all-refreshes',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='Revoke all refresh tokens',
    description="""
        Revokes all refresh tokens associated with the authenticated user,
        invalidating all active refresh-token sessions.
    """,
    responses=revoke_all_refreshes_responses,
)
async def revoke_all_refreshes(
    header_authorization: Annotated[
        HTTPAuthorizationCredentials, Depends(bearer_scheme)
    ],
    use_case: RevokeAllRefreshesDep,
):
    """
    Revokes all refresh tokens associated with the authenticated user,
    invalidating all active refresh-token sessions.

    Args:
        `header_authorization` (`HTTPAuthorizationCredentials`):
            - Authorization header containing the access token used to
              identify the authenticated user whose refresh tokens should
              be revoked.
        `use_case` (`RevokeAllRefreshesDep`):
            - Injected application use case responsible for revoking all
              refresh tokens associated with the authenticated user.

    Raises:
        `InfrastructureError`:
            - If token validation or persistence operations fail.
        `InvalidTokenError`:
            - If token validation fails.
        `InvalidTokenTypeError`:
            - If token type is not a refresh token.
    """
    await use_case.execute(header_authorization.credentials)
