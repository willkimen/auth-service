from datetime import datetime, timedelta, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
)
from application.messages.email_payloads import DeleteAccountPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.entities.verification_code_factory import new_delete_account_code
from domain.exceptions import InactiveUserError
from domain.value_objects.code import Code


class DeleteCodeUseCase:
    """
    Generates and persists a verification code used to authorize
    the account deletion process for an authenticated user.

    The flow validates the provided access token, verifies if the
    token exists and is not revoked, retrieves the authenticated
    user, validates the user state, generates a delete-account
    verification code, and persists both the code and the
    notification message inside a transactional boundary.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation and decoding.
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

    async def execute(self, access: str, code_expiration_time: int):
        """
        Initializes the delete account code generation use case.

        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

        Raises:
            `InvalidTokenError`:
                - Raised when the provided token is invalid, expired,
                  malformed, or contains invalid claims.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `TokenNotFoundError`:
                - Raised when the token JTI does not exist in persistence.
            `TokenRevokedError`:
                - Raised when the token was revoked.
            `UserNotFoundError`:
                - Raised when the authenticated user no longer exists.
            `InactiveUserError`:
                - Raised when the authenticated user is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted user data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - Raised when persistence operations, token operations,
                  transaction handling, or external infrastructure services
                  fail unexpectedly.
        """
        token_payload: PayloadTokenDTO = self.token_manager.validate(access)

        if token_payload.typ != 'access':
            raise InvalidTokenTypeError()

        if not await self.uow.token_repo.exists(token_payload.jti):
            raise TokenNotFoundError()

        if await self.uow.token_repo.is_revoked(token_payload.jti):
            raise TokenRevokedError()

        user: User | None = await self.uow.user_repo.get_by_public_id(
            token_payload.sub
        )

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise InactiveUserError()

        verification_code: VerificationCode = new_delete_account_code(
            user_public_id=user.public_id,
            code=Code.generate(),
            created_at=datetime.now(timezone.utc),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=code_expiration_time)
            ),
        )

        payload = DeleteAccountPayload(
            to=user.email.value,
            code=verification_code.code.value,
            expiration=str(code_expiration_time),
        )

        message = Message(
            type=MessageType.DELETE_CODE,
            payload=payload,
            expires_at=verification_code.expires_at,
        )

        # Persist related changes atomically as a single unit of work.
        async with self.uow:
            await self.uow.code_repo.create(verification_code)
            await self.uow.message_repo.create(message)
