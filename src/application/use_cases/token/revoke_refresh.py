from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import InvalidTokenTypeError
from application.ports.output import TokenManagerPort, TokenRepositoryPort


class RevokeRefreshUseCase:
    """
    Handles the refresh token revocation workflow.

    This use case validates the provided refresh token and marks
    the associated refresh token as revoked in persistence storage.

    Args:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation.
        `token_repo` (TokenRepositoryPort):
            - Repository responsible for refresh token persistence and
              revocation operations.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        token_repo: TokenRepositoryPort,
    ):
        self.token_manager = token_manager
        self.token_repo = token_repo

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

        await self.token_repo.revoke_refresh(token_payload.jti)
