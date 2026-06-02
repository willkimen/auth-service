from application.dtos.token_dto import PayloadTokenDTO
from application.dtos.user_dto import UserPublicDTO
from application.exceptions import (
    InvalidTokenTypeError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
)
from application.ports.output import (
    TokenManagerPort,
    TokenRepositoryPort,
    UserRepositoryPort,
)
from domain.entities.user import User
from domain.exceptions import InactiveUserError


class DetailUseCase:
    """
    Retrieves authenticated user details from a valid access token.

    The use case validates the token, verifies token persistence
    and revocation status, retrieves the associated user, validates
    the user's state, and returns a public-safe representation of
    the user.

    Attributes:
        `user_repo` (UserRepositoryPort):
            - Port/Interface responsible for user data retrieval
              operations.
        `token_repo` (TokenRepositoryPort):
            - Port/Interface responsible for token persistence and
              revocation queries.
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token validation and
              payload extraction.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        token_repo: TokenRepositoryPort,
        token_manager: TokenManagerPort,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.token_manager = token_manager

    async def execute(self, access: str) -> UserPublicDTO:
        """
        Validates an access token and returns the associated user's
        public information.

        The token must exist, must not be revoked, and must reference
        an active user account.

        Args:
            `access` (str):
                - Authenticated access token associated with the user.

        Returns:
            `UserPublicDTO`:
                - Public-safe representation of the authenticated user.

        Raises:
            `InvalidTokenError`:
                - Raised when token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `TokenNotFoundError`:
                - If the validated token does not exist in persistence.
            `TokenRevokedError`:
                - If the token has been revoked.
            `UserNotFoundError`:
                - If no user exists for the token subject.
            `InactiveUserError`:
                - If user account is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output
                  adapter (infrastructure layer).
        """
        token_payload: PayloadTokenDTO = self.token_manager.validate(access)

        if token_payload.typ != 'access':
            raise InvalidTokenTypeError()

        if not await self.token_repo.exists(token_payload.jti):
            raise TokenNotFoundError()

        if await self.token_repo.is_revoked(token_payload.jti):
            raise TokenRevokedError()

        user: User | None = await self.user_repo.get_by_public_id(
            token_payload.sub
        )

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise InactiveUserError()

        return UserPublicDTO.from_entity(user)
