from datetime import datetime, timezone

from auth_service.application.exceptions import (
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from auth_service.application.messages.email_payloads import (
    EmailNotificationPayload,
)
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_types import MessageType
from auth_service.application.ports.output import UnitOfWorkPort
from auth_service.domain.entities.user import User
from auth_service.domain.entities.verification_code import VerificationCode
from auth_service.domain.enums import CodeType
from auth_service.domain.exceptions import (
    EmailAlreadyVerifiedError,
    InactiveUserError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)


class EmailVerificationUseCase:
    """
    Completes the user's email verification process by validating the
    verification code issued for this purpose.

    The verification code acts as a temporary credential that
    authorizes the user to confirm ownership of the email address.
    Once the verification succeeds, the user's email is marked as
    verified, and the data required to notify the user of the
    successful verification is persisted for subsequent processing.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the email verification.
    """

    def __init__(
        self,
        uow: UnitOfWorkPort,
    ):
        self.uow = uow

    async def execute(self, email: str, code: str):
        """
        Completes the user's email verification by validating the
        verification code issued for the email address.

        The user must exist, have an active account, and not have an
        already verified email address. The verification code must be
        valid for the user, unused, issued for email verification,
        and not expired. The user's email is then marked as verified,
        and the data required to notify the user of the successful
        verification is persisted for subsequent processing.

        Args:
            `email` (str):
                - Email address associated with the user whose email
                  ownership is being verified.
            `code` (str):
                - Verification code provided by the user to confirm
                  ownership of the email address.

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

        async with self.uow:
            user: User | None = await self.uow.users.get_by_email(email)

            if user is None:
                raise UserNotFoundError()

            if user.email_verified is True:
                raise EmailAlreadyVerifiedError()

            if user.is_active is False:
                raise InactiveUserError()

            verification_code: (
                VerificationCode | None
            ) = await self.uow.codes.get_by_user_id_and_code(
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

            payload = EmailNotificationPayload(user.email.value)

            message = Message(
                type=MessageType.NOTIFY_EMAIL_VERIFIED,
                payload=payload,
            )

            await self.uow.users.update(user)
            await self.uow.codes.mark_as_used(verification_code)
            await self.uow.messages.create(message)
