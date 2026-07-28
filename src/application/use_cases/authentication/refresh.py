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
    Issues a new access token for an authenticated session using a
    valid refresh token.

    The refresh token must be valid, correspond to an existing and
    non-revoked session, and identify an existing user with an active
    account. When these conditions are satisfied, a new access token
    is issued for the authenticated session.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating refresh tokens and
              generating new access tokens.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the operations
              required to validate the refresh token and retrieve
              the authenticated user.
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
        Issues a new access token for the session identified by the
        provided refresh token.

        The refresh token must be valid, be a refresh token, correspond
        to an existing and non-revoked session, and identify an
        existing user with an active account. A new access token is
        then issued for the authenticated user.

        Args:
            `refresh` (str):
                - Refresh token used to authenticate the session and
                  obtain a new access token.

        Returns:
            `str`:
                - Newly issued access token for the authenticated
                  user's session.

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
