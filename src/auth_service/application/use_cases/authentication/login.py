from datetime import datetime
from zoneinfo import ZoneInfo

from auth_service.application.dtos.token_dto import PairTokensDTO
from auth_service.application.exceptions import (
    InvalidCredentialsError,
)
from auth_service.application.ports.output import (
    HasherPort,
    TokenManagerPort,
    UnitOfWorkPort,
)
from auth_service.domain.entities.user import User
from auth_service.domain.exceptions import (
    InactiveUserError,
    UnverifiedEmailError,
)


class LoginUseCase:
    """
    Authenticates a user using their email address and password and
    establishes an authenticated session by issuing access and refresh
    tokens.

    Authentication succeeds only when the user exists, the provided
    password is valid, the account is active, and the user's email
    address has been verified. After successful authentication, the
    user's login state is updated, and the refresh token is persisted
    to support subsequent session validation and revocation.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for generating authentication tokens
              and managing token-related session operations.
        `hasher` (HasherPort):
            - Port responsible for securely verifying the provided
              password against the stored password hash.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to authenticate the user and
              establish the authenticated session.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        hasher: HasherPort,
        uow: UnitOfWorkPort,
    ):
        self.token_manager = token_manager
        self.hasher = hasher
        self.uow = uow

    async def execute(self, email: str, password: str) -> PairTokensDTO:
        """
        Authenticates the user and establishes an authenticated session.

        The user must exist, the provided password must match the stored
        password, the account must be active, and the user's email
        address must be verified. After successful authentication, the
        user's login state is updated and a pair of access and refresh
        tokens is issued. The refresh token is persisted to support
        subsequent session validation and revocation.

        Args:
            `email` (str):
                - Email address used to identify the user account.
            `password` (str):
                - Plain-text password provided by the user for
                  authentication.

        Returns:
            `PairTokensDTO`:
                - Pair containing the access and refresh tokens issued
                  for the authenticated session.

        Raises:
            `InvalidCredentialsError`:
                - If user does not exist or password is invalid.
            `InactiveUserError`:
                - If user account is inactive.
            `UnverifiedEmailError`:
                - If user email has not been verified.
            `InfrastructureError`:
                - If repository, hashing, or token generation fails.
        """

        async with self.uow:
            user: User | None = await self.uow.users.get_by_email(email)

            if user is None:
                raise InvalidCredentialsError()

            if not self.hasher.verify_password(
                plain_password=password,
                hashed_password=user.hash_password.value,
            ):
                raise InvalidCredentialsError()

            if not user.is_active:
                raise InactiveUserError()

            if not user.email_verified:
                raise UnverifiedEmailError()

            user.record_login()

            pair_tokens: PairTokensDTO = self.token_manager.new_pair_token(
                user.public_id
            )

            # convert unix timestamp to datatime aware
            exp = datetime.fromtimestamp(
                pair_tokens.refresh.payload.exp,
                tz=ZoneInfo('UTC'),
            )

            await self.uow.users.update(user)
            await self.uow.tokens.create(
                pair_tokens.refresh.payload.sub,
                pair_tokens.refresh.payload.jti,
                exp,
            )

            return pair_tokens
