from application.dtos.token_dto import PayloadTokenDTO
from application.ports.output import TokenManagerPort, TokenRepositoryPort


class RevokeAllRefreshesUseCase:
    """
    Handles the refresh token mass revocation workflow.

    This use case validates the provided refresh token and revokes
    all refresh tokens associated with the authenticated user,
    invalidating every active authenticated session for that user.

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

    async def execute(self, token: str):
        """
        Executes the mass refresh token revocation flow.

        This operation revokes every refresh token associated with
        the authenticated user identified by the provided token.

        Args:
            `token` (str):
                - Refresh token.

        Raises:
            `InfrastructureError`:
                - If token validation or persistence operations fail.
            `TokenError`:
                - If token validation fails.
        """
        token_payload: PayloadTokenDTO = self.token_manager.validate(token)
        await self.token_repo.revoke_all_refreshes(token_payload.sub)
