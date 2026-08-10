from datetime import datetime, timedelta, timezone

from auth_service.application.exceptions import UserNotFoundError
from auth_service.application.messages.email_payloads import EmailCodePayload
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_types import MessageType
from auth_service.application.ports.output import UnitOfWorkPort
from auth_service.domain.entities.user import User
from auth_service.domain.entities.verification_code import VerificationCode
from auth_service.domain.entities.verification_code_factory import (
    new_reset_password_code,
)
from auth_service.domain.exceptions import InactiveUserError
from auth_service.domain.value_objects.code import Code


class ResetPasswordCodeUseCase:
    """
    Initiates the password reset process for a user account by
    generating a temporary verification code for the password reset
    operation.

    The verification code acts as a temporary credential that can
    later be used to authorize the password reset. The code and the
    data required to deliver it to the user are persisted for
    subsequent processing.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the password reset
              verification process.
    """

    def __init__(self, uow: UnitOfWorkPort):
        self.uow = uow

    async def execute(
        self,
        email: str,
        code_expiration_time: int,
    ):
        """
        Initiates the password reset process by generating a temporary
        verification code for the user's account.

        The user must exist and have an active account. A verification
        code with a limited validity period is then generated and
        persisted together with the data required to deliver the code
        to the user.

        Args:
            `email` (str):
                - Email address associated with the user account whose
                  password is being reset.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

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

        async with self.uow:
            user: User | None = await self.uow.users.get_by_email(email)

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
                    datetime.now(timezone.utc) + timedelta(minutes=code_expiration_time)
                ),
            )

            payload = EmailCodePayload(
                to=user.email.value,
                code=verification_code.code.value,
            )

            message = Message(
                type=MessageType.RESET_PASSWORD_CODE,
                payload=payload,
                expires_at=verification_code.expires_at,
            )

            await self.uow.codes.create(verification_code)
            await self.uow.messages.create(message)
