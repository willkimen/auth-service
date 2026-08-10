from datetime import datetime, timedelta, timezone

from auth_service.application.exceptions import UserNotFoundError
from auth_service.application.messages.email_payloads import EmailCodePayload
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_types import MessageType
from auth_service.application.ports.output import UnitOfWorkPort
from auth_service.domain.entities.user import User
from auth_service.domain.entities.verification_code import VerificationCode
from auth_service.domain.entities.verification_code_factory import (
    new_email_verification_code,
)
from auth_service.domain.exceptions import (
    EmailAlreadyVerifiedError,
    InactiveUserError,
)
from auth_service.domain.value_objects.code import Code


class EmailVerificationCodeUseCase:
    """
    Initiates the email verification process for a user account by
    generating a temporary verification code for the user's email
    address.

    The verification code acts as a temporary credential that can
    later be used to confirm ownership of the email address. The
    code and the data required to deliver it to the user are
    persisted for subsequent processing.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the email verification
              process.
    """

    def __init__(self, uow: UnitOfWorkPort):
        self.uow = uow

    async def execute(
        self,
        email: str,
        code_expiration_time: int,
    ):
        """
        Initiates the email verification process by generating a
        temporary verification code for the user's email address.

        The user must exist, have an active account, and not have an
        already verified email address. A verification code with a
        limited validity period is then generated and persisted
        together with the data required to deliver the code to the
        user.

        Args:
            `email` (str):
                - Email address used to identify the account whose
                  ownership is being verified.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

        Raises:
            `UserNotFoundError`:
                - If no user exists with the provided email.
            `EmailAlreadyVerifiedError`:
                - If user's email is already verified.
            `InactiveUserError`:
                - If user account is inactive.
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

            if user.email_verified:
                raise EmailAlreadyVerifiedError()

            if not user.is_active:
                raise InactiveUserError()

            # When creating a new verification code.
            verification_code: VerificationCode = new_email_verification_code(
                user_public_id=user.public_id,
                code=Code.generate(),
                created_at=datetime.now(timezone.utc),
                expires_at=(
                    datetime.now(timezone.utc) + timedelta(minutes=code_expiration_time)
                ),
            )

            payload = EmailCodePayload(
                to=user.email.value,
                code=verification_code.code.value,
            )

            message = Message(
                type=MessageType.EMAIL_VERIFICATION_CODE,
                payload=payload,
                expires_at=verification_code.expires_at,
            )

            await self.uow.codes.create(verification_code)
            await self.uow.messages.create(message)
