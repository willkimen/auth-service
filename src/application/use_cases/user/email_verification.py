from datetime import datetime, timezone

from application.exceptions import (
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import EmailVerifiedPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import UnitOfWorkPort
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    EmailAlreadyVerifiedError,
    InactiveUserError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)


class EmailVerificationUseCase:
    """
    Completes the user email verification process.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(
        self,
        uow: UnitOfWorkPort,
    ):
        self.uow = uow

    async def execute(self, email: str, code: str):
        """
        Verifies a user's email using a verification code and
        registers an notification message.

        This method:
            - Retrieves the user and verification code.
            - Validates user and verification code.
            - Marks the user as verified.
            - Marks the verification code as used.
            - Persists a notification message informing the user about
              the successful email verified.

        Args:
            `email` (str):
                - User email address associated with the account.
            `code` (str):
                - Verification code informed by the user.

        Raises:
            `UserNotFoundError`:
                - If no user exists with the provided email.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist for the user and code.
            `EmailAlreadyVerifiedError`:
                - If user's email is already verified.
            `InactiveUserError`:
                - If user account is inactive.
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
                - If an unexpected failure occurs within an output adapter
                  (infrastructure layer)
        """
        user: User | None = await self.uow.user_repo.get_by_email(email)

        if user is None:
            raise UserNotFoundError()

        if user.email_verified is True:
            raise EmailAlreadyVerifiedError()

        if user.is_active is False:
            raise InactiveUserError()

        verification_code: (
            VerificationCode | None
        ) = await self.uow.code_repo.get_by_user_id_and_code(
            user.public_id,
            code,
        )

        if verification_code is None:
            raise VerificationCodeNotFoundError()

        if verification_code.is_used():
            raise VerificationCodeAlreadyUsedError()

        if verification_code.type is not CodeType.EMAIL_VERIFICATION:
            raise VerificationCodeTypeError()

        if verification_code.is_expired(datetime.now(timezone.utc)):
            raise VerificationCodeExpiredError()

        verification_code.mark_as_used(datetime.now(timezone.utc))

        user.mark_email_as_verified()

        payload = EmailVerifiedPayload(user.email.value)

        message = Message(
            type=MessageType.NOTIFICATION_EMAIL_VERIFIED,
            payload=payload,
        )

        # Persist related changes atomically as a single unit of work.
        async with self.uow:
            await self.uow.user_repo.update(user)
            await self.uow.code_repo.mark_as_used(verification_code)
            await self.uow.message_repo.create(message)
