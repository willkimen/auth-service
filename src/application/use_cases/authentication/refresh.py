from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
)
from application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)
from domain.entities.user import User
from domain.exceptions import InactiveUserError


class RefreshUseCase:
    """
    Handles the refresh access token workflow.

    This use case validates the provided refresh token, verifies
    whether the token exists and is not revoked, validates the
    authenticated user state, and generates a new access token
    for the authenticated session.

    Args:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation and generation.
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

    async def execute(self, refresh: str) -> str:
        """
        Executes the refresh access token flow.

        Args:
            `refresh` (str):
                - Refresh token.

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
        async with self.uow:
            token_payload: PayloadTokenDTO = self.token_manager.validate(
                refresh
            )

            if token_payload.typ != 'refresh':
                raise InvalidTokenTypeError()

            if not await self.uow.tokens.exists(token_payload.jti):
                raise TokenNotFoundError()

            if await self.uow.tokens.is_revoked(token_payload.jti):
                raise TokenRevokedError()

            user: User | None = await self.uow.users.get_by_public_id(
                token_payload.sub
            )

            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise InactiveUserError()

            return self.token_manager.new_access(user.public_id)
