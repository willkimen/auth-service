from datetime import datetime, timezone

from application.exceptions import (
    PasswordMismatchError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import EmailNotificationPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    HasherPort,
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


class ResetPasswordUseCase:
    """
    Completes the password reset process for a user account by
    validating the verification code issued for this operation.

    The verification code acts as a temporary credential that
    authorizes the user to reset their password. Once the verification
    succeeds, the user's password is changed, active authentication
    sessions are invalidated, and the data required to notify the user
    of the password reset is persisted for subsequent processing.

    Attributes:
        `hasher` (HasherPort):
            - Port responsible for securely hashing the user's new
              password before it is stored.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the password reset.
    """

    def __init__(
        self,
        hasher: HasherPort,
        uow: UnitOfWorkPort,
    ):
        self.hasher = hasher
        self.uow = uow

    async def execute(
        self,
        email: str,
        code: str,
        raw_password: str,
        raw_password_confirmation: str,
    ):
        """
        Completes the password reset process by validating the new
        password and the verification code issued for the operation.

        The user must exist and have an active account. The new
        password must satisfy the password policy and match its
        confirmation. The verification code must be valid for the
        user, unused, issued for the password reset operation, and
        not expired. The user's password is then changed, active
        authentication sessions are invalidated, and the data
        required to notify the user of the password reset is
        persisted for subsequent processing.

        Args:
            `email` (str):
                - Email address associated with the user account
                  whose password is being reset.
            `code` (str):
                - Verification code issued for the password reset
                  operation.
            `raw_password` (str):
                - New plain-text password provided by the user. It is
                  validated against the password policy and securely
                  hashed before being persisted.
            `raw_password_confirmation` (str):
                - Confirmation of the new password used to verify
                  that both password values match.

        Raises:
            `InvalidPasswordError`:
                - Raised when the password does not satisfy the
                  password policy.
            `PasswordMismatchError`:
                - Raised when password and confirmation password do
                  not match.
            `UserNotFoundError`:
                - If no user exists with the provided email.
            `InactiveUserError`:
                - If user account is inactive.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist for the user
                  and code.
            `VerificationCodeAlreadyUsedError`:
                - If verification code was already used.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
            `VerificationCodeTypeError`:
                - If verification code type is incorrect.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output
                  adapter (infrastructure layer)
        """

        async with self.uow:
            PasswordPolicy.validate(raw_password)

            if raw_password != raw_password_confirmation:
                raise PasswordMismatchError()

            # Retorna
            user: User | None = await self.uow.users.get_by_email(email)

            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise InactiveUserError()

            password_hash_vo = PasswordHash(self.hasher.hash(raw_password))

            verification_code: (
                VerificationCode | None
            ) = await self.uow.codes.get_by_user_id_and_code(
                user.public_id, code
            )

            if verification_code is None:
                raise VerificationCodeNotFoundError()

            if verification_code.is_used():
                raise VerificationCodeAlreadyUsedError()

            if not verification_code.type == CodeType.RESET_PASSWORD:
                raise VerificationCodeTypeError()

            if verification_code.is_expired(datetime.now(timezone.utc)):
                raise VerificationCodeExpiredError()

            verification_code.mark_as_used(datetime.now(timezone.utc))

            user.change_password(password_hash_vo)

            message = Message(
                type=MessageType.NOTIFY_PASSWORD_RESET,
                payload=EmailNotificationPayload(user.email.value),
            )

            await self.uow.users.update(user)
            await self.uow.codes.mark_as_used(verification_code)
            await self.uow.tokens.revoke_all(user.public_id)
            await self.uow.messages.create(message)
