from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import InvalidTokenTypeError
from application.ports.output import TokenManagerPort, UnitOfWorkPort


class RevokeRefreshUseCase:
    """
    Handles the refresh token revocation workflow.

    This use case validates the provided refresh token and marks
    the associated refresh token as revoked in persistence storage.

    Args:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
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
        Executes the refresh token revocation flow.

        Args:
            `refresh` (str):
                - Refresh token.

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
            await self.uow.token_repo.revoke(token_payload.jti)
