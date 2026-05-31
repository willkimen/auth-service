from datetime import datetime, timedelta, timezone

from application.exceptions import UserNotFoundError
from application.messages.email_payloads import ResetPasswordPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import UnitOfWorkPort
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.entities.verification_code_factory import new_reset_password_code
from domain.exceptions import InactiveUserError
from domain.value_objects.code import Code


class ResetPasswordCodeUseCase:
    """
    Starts the password reset process for a user account.

    The process is initiated by generating a password reset
    verification code, persisting it, and persisting the data
    required to notify the user through a message.

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
        """
        Generates a password reset verification code and persists
        the notification message required to deliver it to the user.

        Args:
            `email` (str):
                - User email address associated with the account.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

        Raises:
            `UserNotFoundError`:
                - If no user exists with the provided email.
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

        if not user.is_active:
            raise InactiveUserError()

        # Newly generated reset password codes must start as unused.
        verification_code: VerificationCode = new_reset_password_code(
            user_public_id=user.public_id,
            code=Code.generate(),
            created_at=datetime.now(timezone.utc),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=code_expiration_time)
            ),
        )

        payload = ResetPasswordPayload(
            to=user.email.value,
            code=verification_code.code.value,
            expiration=str(code_expiration_time),
        )

        message = Message(
            type=MessageType.PASSWORD_RESET_CODE, payload=payload
        )

        # Persist related changes atomically as a single unit of work.
        async with self.uow:
            await self.uow.code_repo.create(verification_code)
            await self.uow.message_repo.create(message)
