from datetime import datetime, timedelta, timezone

from application.exceptions import UserNotFoundError
from application.messages.email_payloads import EmailCodePayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import UnitOfWorkPort
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.entities.verification_code_factory import (
    new_email_verification_code,
)
from domain.exceptions import EmailAlreadyVerifiedError, InactiveUserError
from domain.value_objects.code import Code


class EmailVerificationCodeUseCase:
    """
    Starts the email verification process for a user account.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(self, uow: UnitOfWorkPort):
        self.uow = uow

    async def execute(
        self,
        email: str,
        code_expiration_time: int,
    ):
        """Generates a code and persists an email verification message.

        This method:
            - Creating the verification code and persisting it in the database.
            - Retrieves and validate user.
            - Persists a message containing the data required to send
              the verification code.

        Args:
            `email` (str):
                - User email address used to identify the account.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

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
        user: User | None = await self.uow.user_repo.get_by_email(email)

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
                datetime.now(timezone.utc)
                + timedelta(minutes=code_expiration_time)
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

        # Persist related changes atomically as a single unit of work.
        async with self.uow:
            await self.uow.code_repo.create(verification_code)
            await self.uow.message_repo.create(message)
