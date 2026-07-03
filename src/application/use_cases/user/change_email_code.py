from datetime import datetime, timedelta, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
)
from application.messages.email_payloads import EmailCodePayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.entities.verification_code_factory import new_change_email_code
from domain.exceptions import InactiveUserError
from domain.value_objects.code import Code
from domain.value_objects.email import Email


class ChangeEmailCodeUseCase:
    """
    Initializes the email change verification process for
    an authenticated user.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token validation and payload
              extraction.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        self.token_manager = token_manager
        self.uow = uow

    async def execute(
        self,
        access: str,
        new_email: str,
        code_expiration_time: int,
    ):
        """
        Generates and persists an email change verification code for
        the authenticated user.

        This method:
            - Validates the authentication access token.
            - Validates the email address.
            - Verifies token state and existence.
            - Retrieves the authenticated user
            - Generates a verification code for the new email address.
            - Persists the verification code.
            - Persists a message containing the data required to send
              the verification code.

        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `new_email` (str):
                - New email address requested by the user.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

        Raises:
            `InvalidEmailError`:
                - Raised when the provided email is invalid.
            `InvalidTokenError`:
                - Raised when token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `TokenNotFoundError`:
                - Raised when token does not exist in persistence layer.
            `TokenRevokedError`:
                - Raised when token has already been revoked.
            `UserNotFoundError`:
                - Raised when no user exists for the authenticated token.
            `InactiveUserError`:
                - Raised when the authenticated user is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - Raised when an unexpected infrastructure failure occurs
                  within an output adapter.
        """

        async with self.uow:
            email_vo = Email(new_email)

            token_payload: PayloadTokenDTO = self.token_manager.validate(
                access
            )

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

            verification_code: VerificationCode | None = new_change_email_code(
                user_public_id=user.public_id,
                code=Code.generate(),
                created_at=datetime.now(timezone.utc),
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(minutes=code_expiration_time)
                ),
                new_email=email_vo.value,
            )

            message = Message(
                type=MessageType.CHANGE_EMAIL_CODE,
                payload=EmailCodePayload(
                    to=email_vo.value,
                    code=verification_code.code.value,
                ),
                expires_at=verification_code.expires_at,
            )

            await self.uow.code_repo.create(verification_code)
            await self.uow.message_repo.create(message)
