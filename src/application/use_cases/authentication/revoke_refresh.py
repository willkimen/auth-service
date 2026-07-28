from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import InvalidTokenTypeError
from application.ports.output import TokenManagerPort, UnitOfWorkPort


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
