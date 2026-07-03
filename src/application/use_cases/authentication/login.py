from datetime import datetime
from zoneinfo import ZoneInfo

from application.dtos.token_dto import PairTokensDTO
from application.exceptions import (
    InvalidCredentialsError,
)
from application.ports.output import (
    HasherPort,
    TokenManagerPort,
    UnitOfWorkPort,
)
from domain.entities.user import User
from domain.exceptions import InactiveUserError, UnverifiedEmailError


class LoginUseCase:
    """
    Handles user authentication and issues access/refresh tokens.

    This use case is responsible for validating user credentials,
    ensuring account state is valid, updating user persistence state,
    generating authentication tokens, and persisting refresh token
    metadata for session continuity.

    The flow enforces strict authentication rules:
    - User existence validation
    - Password verification
    - Account activation check
    - Email verification check

    After successful validation, the use case:
    - Updates the user entity (e.g., last login or metadata changes)
    - Generates a new pair of tokens (access + refresh)
    - Persists the refresh token for later validation/revocation

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token generation and
            session management.
        `hasher` (HasherPort):
            - Port/Interface responsible for securely verifying raw passwords.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
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
        Executes the authentication flow.

        Args:
            `email` (str):
                - User email used for authentication lookup.
            `password` (str):
                - Plain password provided by the user.

        Returns:
            `PairTokensDTO`:
                - Access and refresh tokens for authenticated session.

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
