from datetime import datetime, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import EmailNotificationPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    InactiveUserError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)
from domain.value_objects.email import Email


class ChangeEmailUseCase:
    """
    Completes the user email change process using a previously
    generated verification code associated with an authenticated
    session.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token validation and
              payload extraction.
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

    async def execute(self, access: str, code: str):
        """
        Changes the authenticated user's email address after
        validating a previously generated email change verification
        code.

        This method:
            - Validates the authenticated token.
            - Checks whether the token exists and is not revoked.
            - Validates the verification code state
            - Updates the user's email address.
            - Revokes all active refresh tokens.
            - Persists a notification message informing the user about
              the successful email change.

        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code` (str):
                - Verification code sent to the new email address.

        Raises:
            `InvalidTokenError`:
                - If the provided token is malformed, invalid,
                  expired, or cannot be decoded.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `TokenNotFoundError`:
                - If the token identifier does not exist in the
                  persistence layer.
            `TokenRevokedError`:
                - If the token has been revoked.
            `VerificationCodeNotFoundError`:
                - If no verification code exists for the user and
                  provided code.
            `VerificationCodeAlreadyUsedError`:
                - If the verification code was already used.
            `VerificationCodeTypeError`:
                - If the verification code type is invalid for the
                  email change operation.
            `VerificationCodeExpiredError`:
                - If the verification code has expired.
            `UserNotFoundError`:
                - If no user exists for the authenticated token.
            `InactiveUserError`:
                - If the user account is inactive.
            `InvalidEmailError`:
                - If the email extracted from the verification code
                  is invalid.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain entities or value objects.
            `InfrastructureError`:
                - If an unexpected failure occurs in the infrastructure
                  layer during repository, token, or persistence
                  operations.
        """
        async with self.uow:
            token_payload: PayloadTokenDTO = self.token_manager.validate(
                access
            )

            if token_payload.typ != 'access':
                raise InvalidTokenTypeError()

            if not await self.uow.tokens.exists(token_payload.jti):
                raise TokenNotFoundError()

            if await self.uow.tokens.is_revoked(token_payload.jti):
                raise TokenRevokedError()

            verification_code: (
                VerificationCode | None
            ) = await self.uow.codes.get_by_user_id_and_code(
                token_payload.sub, code
            )

            if verification_code is None:
                raise VerificationCodeNotFoundError()

            if verification_code.is_used():
                raise VerificationCodeAlreadyUsedError()

            if not verification_code.type == CodeType.CHANGE_EMAIL:
                raise VerificationCodeTypeError()

            if verification_code.is_expired(datetime.now(timezone.utc)):
                raise VerificationCodeExpiredError()

            verification_code.mark_as_used(datetime.now(timezone.utc))

            user: User | None = await self.uow.users.get_by_public_id(
                token_payload.sub
            )

            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise InactiveUserError()

            new_email = verification_code.get_new_email()
            new_email_vo: Email = Email(new_email)
            user.change_email(new_email_vo)

            message = Message(
                type=MessageType.NOTIFY_EMAIL_CHANGED,
                payload=EmailNotificationPayload(to=user.email.value),
            )

            await self.uow.users.update(user)
            await self.uow.codes.mark_as_used(verification_code)
            await self.uow.messages.create(message)
            await self.uow.tokens.revoke_all(user.public_id)
