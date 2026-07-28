from datetime import datetime, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
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
    Completes the authenticated user's email change process by
    validating the verification code issued for this operation.

    The verification code acts as a temporary credential that
    authorizes the user to complete the email change. Once the
    verification succeeds, the user's email address is changed,
    active authentication sessions are invalidated, and the data
    required to notify the user of the change is persisted for
    subsequent processing.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the email change.
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
        Completes the authenticated user's email change by validating
        the verification code issued for the operation.

        The verification code must be valid for the authenticated user,
        unused, issued for the email change operation, and not expired.
        The new email address associated with the verified operation is
        then applied to the user's account.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting the email change.
            `code` (str):
                - Verification code issued for the email change
                  operation and sent to the new email address.

        Raises:
            `InvalidTokenError`:
                - If the provided token is malformed, invalid,
                  expired, or cannot be decoded.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
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
