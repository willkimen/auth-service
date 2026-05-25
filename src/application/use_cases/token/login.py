from application.dtos.token_dto import PairTokensDTO
from application.exceptions import (
    InvalidCredentialsError,
)
from application.ports.output import (
    HasherPort,
    TokenManagerPort,
    TokenRepositoryPort,
    UserRepositoryPort,
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
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        token_repo: TokenRepositoryPort,
        token_manager: TokenManagerPort,
        hasher: HasherPort,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.token_manager = token_manager
        self.hasher = hasher

    async def execute(self, email: str, password: str) -> PairTokensDTO:
        """
        Executes the authentication flow.

        Args:
            email:
                User email used for authentication lookup.
            password:
                Plain password provided by the user.

        Returns:
            PairTokensDTO:
                Access and refresh tokens for authenticated session.

        Raises:
            InvalidCredentialsError:
                If user does not exist or password is invalid.
            InactiveUserError:
                If user account is inactive.
            UnverifiedEmailError:
                If user email has not been verified.
            InfrastructureError:
                If repository, hashing, or token generation fails.
        """
        user: User | None = await self.user_repo.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError()

        if not self.hasher.verify_password(
            plain_password=password, hashed_password=user.hash_password.value
        ):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        if not user.email_verified:
            raise UnverifiedEmailError()

        await self.user_repo.update(user)

        pair_tokens: PairTokensDTO = self.token_manager.new_pair_token(
            user.public_id
        )

        # InfrastructureError
        await self.token_repo.save_refresh(
            pair_tokens.refresh.payload.sub,
            pair_tokens.refresh.payload.jti,
            pair_tokens.refresh.payload.expires_at,
        )

        return pair_tokens
