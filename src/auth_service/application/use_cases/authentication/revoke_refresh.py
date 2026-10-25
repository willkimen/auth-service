"""
Design rationale:
This use case revokes a specific refresh token without requiring an
authenticated access token. The refresh token itself identifies the
credential to be revoked and must be validated before the operation
proceeds.

This design is inspired by RFC 7009 (OAuth 2.0 Token Revocation),
which defines a mechanism for revoking individual tokens. However,
RFC 7009 does not mandate this specific authentication policy or
require a separate endpoint for revoking all refresh tokens.

Revoking all refresh tokens is handled by a separate use case that
requires an authenticated access token to identify the user whose
tokens are to be revoked. This prevents the operation from affecting
tokens belonging to other users.

The distinction is intentional: revoking a specific token targets a
credential supplied by the caller, whereas revoking all tokens
targets a user's collection of credentials and therefore requires
an authenticated identity.

"""

from auth_service.application.dtos.token_dto import PayloadTokenDTO
from auth_service.application.exceptions import InvalidTokenTypeError
from auth_service.application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)


class RevokeRefreshUseCase:
    """
    Revokes a specific refresh token associated with an authenticated
    session.

    The refresh token must be valid and be a refresh token before it
    can be revoked. Once revoked, the token can no longer be used to
    obtain new access tokens for the associated session.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the refresh token.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operation required to revoke the refresh token.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        self.token_manager = token_manager
        self.uow = uow

    async def execute(self, refresh: str):
        """
        Revokes the refresh token associated with the provided token.

        The provided token must be valid and be a refresh token. Once
        validated, the token is revoked, preventing it from being used
        to obtain new access tokens for the associated session.

        Args:
            `refresh` (str):
                - Refresh token identifying the session to be revoked.

        Raises:
            `InfrastructureError`:
                - If token validation or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not a refresh token.
        """
        token_payload: PayloadTokenDTO = self.token_manager.validate(refresh)

        if token_payload.typ != 'refresh':
            raise InvalidTokenTypeError()

        # Persist related changes atomically as a single unit of work.
        async with self.uow:
            await self.uow.tokens.revoke(token_payload.jti)
