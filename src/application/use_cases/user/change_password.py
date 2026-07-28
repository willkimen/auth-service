from datetime import datetime, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    PasswordMismatchError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import EmailNotificationPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    HasherPort,
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
from domain.policies.password import PasswordPolicy
from domain.value_objects.password import PasswordHash


class ChangePasswordUseCase:
    """
    Completes the authenticated user's password change process by
    validating the new password and the verification code issued
    for this operation.

    The verification code acts as a temporary credential that
    authorizes the user to complete the password change. Once the
    verification succeeds, the user's password is changed, active
    authentication sessions are invalidated, and the data required
    to notify the user of the change is persisted for subsequent
    processing.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the password change.
        `hasher` (HasherPort):
            - Port responsible for securely hashing the user's
              new password.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
        hasher: HasherPort,
    ):
        self.token_manager = token_manager
        self.uow = uow
        self.hasher = hasher

    async def execute(
        self,
        access: str,
        code: str,
        new_password: str,
        new_password_confirmation: str,
    ):
        """
        Completes the authenticated user's password change by
        validating the new password and the verification code issued
        for the operation.

        The new password must satisfy the password policy and match
        its confirmation. The verification code must be valid for
        the authenticated user, unused, issued for the password
        change operation, and not expired. The user's password is
        then changed, and the data required to notify the user of
        the change is persisted for subsequent processing.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting the password change.
            `code` (str):
                - Verification code issued for the password change
                  operation.
            `new_password` (str):
                - New raw password provided by the user.
            `new_password_confirmation` (str):
                - Confirmation of the new password used to verify
                  that both password values match.

        Raises:
            `InvalidPasswordError`:
                - If password policy validation fails.
            `PasswordMismatchError`:
                - If password confirmation does not match.
            `InfrastructureError`:
                - If hashing, repositories, transactions,
                  or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `UserNotFoundError`:
                - If authenticated user cannot be found.
            `InactiveUserError`:
                - If authenticated user is inactive.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist.
            `VerificationCodeAlreadyUsedError`:
                - If verification code was already consumed.
            `VerificationCodeTypeError`:
                - If verification code type is invalid.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
        """

        async with self.uow:
            PasswordPolicy.validate(new_password)

            if new_password != new_password_confirmation:
                raise PasswordMismatchError()

            hashed_password = self.hasher.hash(new_password)
            password_hash_vo = PasswordHash(hashed_password)

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

            user.change_password(password_hash_vo)

            verification_code: (
                VerificationCode | None
            ) = await self.uow.codes.get_by_user_id_and_code(
                user.public_id, code
            )

            if verification_code is None:
                raise VerificationCodeNotFoundError()

            if verification_code.is_used():
                raise VerificationCodeAlreadyUsedError()

            if not verification_code.type == CodeType.CHANGE_PASSWORD:
                raise VerificationCodeTypeError()

            if verification_code.is_expired(datetime.now(timezone.utc)):
                raise VerificationCodeExpiredError()

            verification_code.mark_as_used(datetime.now(timezone.utc))

            message = Message(
                type=MessageType.NOTIFY_PASSWORD_CHANGED,
                payload=EmailNotificationPayload(user.email.value),
            )

            await self.uow.users.update(user)
            await self.uow.codes.mark_as_used(verification_code)
            await self.uow.tokens.revoke_all(user.public_id)
            await self.uow.messages.create(message)
