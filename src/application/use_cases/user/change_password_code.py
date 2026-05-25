from datetime import datetime, timedelta, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
)
from application.messages.email_payloads import ChangePasswordPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    TokenManagerPort,
    TokenRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.entities.verification_code_factory import new_change_password_code
from domain.exceptions import InactiveUserError
from domain.value_objects.code import Code


class ChangePasswordCodeUseCase:
    """
    Generates and persists a verification code used to authorize a
    password change operation for an authenticated user.

    The flow validates the provided access token, verifies if the
    token exists and is not revoked, retrieves the authenticated
    user, validates the user state, generates a password change
    verification code, and persists both the code and the
    notification message inside a transactional boundary.

    Dependencies:
        user_repo (UserRepositoryPort):
            Repository responsible for retrieving user entities.

        token_repo (TokenRepositoryPort):
            Repository responsible for token persistence and
            revocation checks.

        token_manager (TokenManagerPort):
            Service responsible for token validation and decoding.

        uow (UnitOfWorkPort):
            Transaction manager coordinating persistence operations.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        token_repo: TokenRepositoryPort,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        """
        Initializes the password change code generation use case.

        Args:
            user_repo (UserRepositoryPort):
                Repository used to retrieve user entities.

            token_repo (TokenRepositoryPort):
                Repository used to validate token persistence state.

            token_manager (TokenManagerPort):
                Service responsible for token validation and decoding.

            uow (UnitOfWorkPort):
                Transaction manager coordinating persistence
                operations.

        Raises:
            TokenError:
                Raised when the provided token is invalid, expired,
                malformed, or contains invalid claims.

            TokenNotFoundError:
                Raised when the token JTI does not exist in persistence.

            TokenRevokedError:
                Raised when the token was revoked.

            UserNotFoundError:
                Raised when the authenticated user no longer exists.

            InactiveUserError:
                Raised when the authenticated user is inactive.

            CorruptedPersistenceStateError:
                Raised when persisted user data cannot be reconstructed
                into valid domain objects.

            InfrastructureError:
                Raised when persistence operations, token operations,
                transaction handling, or external infrastructure services
                fail unexpectedly.
        """
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.token_manager = token_manager
        self.uow = uow

    async def execute(self, token: str, code_expiraton_time: int):
        token_payload: PayloadTokenDTO = self.token_manager.validate(token)

        if not await self.token_repo.exists(token_payload.jti):
            raise TokenNotFoundError()

        if await self.token_repo.is_revoke(token_payload.jti):
            raise TokenRevokedError()

        user: User | None = await self.user_repo.get_by_public_id(
            token_payload.sub
        )

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise InactiveUserError()

        verification_code: VerificationCode = new_change_password_code(
            user_public_id=user.public_id,
            code=Code.generate(),
            created_at=datetime.now(timezone.utc),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=code_expiraton_time)
            ),
        )

        payload = ChangePasswordPayload(
            to=user.email.value,
            code=verification_code.code.value,
            expiration=str(code_expiraton_time),
        )

        message = Message(
            type=MessageType.PASSWORD_CHANGE_CODE, payload=payload
        )

        async with self.uow:
            await self.uow.code_repo.create(verification_code)
            await self.uow.message_repo.create(message)
