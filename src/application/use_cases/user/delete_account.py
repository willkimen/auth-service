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


class DeleteAccountUseCase:
    """
    Completes the authenticated user's account deletion process by
    validating the verification code issued for this operation.

    The verification code acts as a temporary credential that
    authorizes the user to complete the account deletion. Once the
    verification succeeds, the user's account and associated
    verification codes are deleted, active authentication sessions
    are invalidated, and the data required to notify the user of the
    deletion is persisted for subsequent processing.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the account deletion.
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
        Completes the authenticated user's account deletion by
        validating the verification code issued for the operation.

        The verification code must be valid for the authenticated user,
        unused, issued for the account deletion operation, and not
        expired. The user's account is then deleted, associated
        verification codes are removed, active authentication sessions
        are invalidated, and the data required to notify the user of
        the deletion is persisted for subsequent processing.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting account deletion.
            `code` (str):
                - Verification code issued for the account deletion
                  operation.

        Raises:
            `InvalidTokenError`:
                - If token validation fails at domain level.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `InfrastructureError`:
                - If token decoding, persistence, or transactional
                  operations fail unexpectedly.
            `UserNotFoundError`:
                - If authenticated user cannot be found.
            `InactiveUserError`:
                - If authenticated user is inactive.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist.
            `VerificationCodeAlreadyUsedError`:
                - If verification code was already consumed.
            `VerificationCodeTypeError`:
                - If verification code is not DELETE_ACCOUNT type.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
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

            verification_code: (
                VerificationCode | None
            ) = await self.uow.codes.get_by_user_id_and_code(
                user.public_id, code
            )

            if verification_code is None:
                raise VerificationCodeNotFoundError()

            if verification_code.is_used():
                raise VerificationCodeAlreadyUsedError()

            if not verification_code.type == CodeType.DELETE_ACCOUNT:
                raise VerificationCodeTypeError()

            if verification_code.is_expired(datetime.now(timezone.utc)):
                raise VerificationCodeExpiredError()

            verification_code.mark_as_used(datetime.now(timezone.utc))

            message = Message(
                type=MessageType.NOTIFY_ACCOUNT_DELETED,
                payload=EmailNotificationPayload(to=user.email.value),
            )

            await self.uow.users.delete(user.public_id)
            await self.uow.codes.delete_all(user.public_id)
            await self.uow.tokens.revoke_all(user.public_id)
            await self.uow.messages.create(message)
