from auth_service.application.dtos.token_dto import PayloadTokenDTO
from auth_service.application.exceptions import InvalidTokenTypeError
from auth_service.application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)


class RevokeAllRefreshesUseCase:
    """
    Revokes all active refresh tokens associated with the
    authenticated user's account.

    This operation invalidates all active authenticated sessions
    associated with the user, requiring the user to authenticate
    again to establish new sessions.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to revoke the user's refresh tokens.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        self.token_manager = token_manager
        self.uow = uow

    async def execute(self, access: str):
        """
        Revokes all active refresh tokens associated with the
        authenticated user identified by the provided access token.

        The provided access token must be valid and be an access token.
        Once the authenticated user is identified, all of their active
        refresh tokens are revoked, invalidating their active
        authenticated sessions.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user whose refresh tokens will be revoked.

        Raises:
            `InfrastructureError`:
                - If token validation or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not a access token.
        """
        token_payload: PayloadTokenDTO = self.token_manager.validate(access)

        if token_payload.typ != 'access':
            raise InvalidTokenTypeError()

        # Persist related changes atomically as a single unit of work.
        async with self.uow:
            await self.uow.tokens.revoke_all(token_payload.sub)
