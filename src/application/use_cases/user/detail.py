from application.dtos.token_dto import PayloadTokenDTO
from application.dtos.user_dto import UserPublicDTO
from application.exceptions import (
    InvalidTokenTypeError,
    UserNotFoundError,
)
from application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)
from domain.entities.user import User
from domain.exceptions import InactiveUserError


class DetailUseCase:
    """
    Retrieves the authenticated user's public information.

    The access token identifies the user whose details are requested.
    The user must have a valid access token, an existing account, and
    an active account status for their public information to be
    returned.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the operations
              required to retrieve the authenticated user's data.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        self.token_manager = token_manager
        self.uow = uow

    async def execute(self, access: str) -> UserPublicDTO:
        """
        Retrieves the public information of the authenticated user.

        The provided access token must be valid and identify an
        existing user with an active account. The authenticated
        user's data is then returned as a public representation
        suitable for exposure outside the domain.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user whose public information is requested.

        Returns:
            `UserPublicDTO`:
                - Public representation of the authenticated user.

        Raises:
            `InvalidTokenError`:
                - Raised when token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
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

        async with self.uow:
            token_payload: PayloadTokenDTO = self.token_manager.validate(
                access
            )

            if token_payload.typ != 'access':
                raise InvalidTokenTypeError()

            user: User | None = await self.uow.users.get_by_public_id(
                token_payload.sub
            )

            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise InactiveUserError()

            return UserPublicDTO.from_entity(user)
