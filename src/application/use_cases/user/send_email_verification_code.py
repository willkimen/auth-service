from datetime import datetime, timedelta, timezone

from application.exceptions import UserNotFoundError
from application.messages.email_payloads import EmailVerificationPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import UnitOfWorkPort, UserRepositoryPort
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.entities.verification_code_factory import (
    new_email_verification_code,
)
from domain.exceptions import EmailAlreadyVerifiedError, InactiveUserError
from domain.value_objects.code import Code


class SendEmailVerificationCodeUseCase:
    """
    Starts the email verification process for a user account.

    Retrieves the target user, validates account eligibility for
    email verification, generates a verification code, persists it,
    and persists a message.
    """

    def __init__(self, user_repo: UserRepositoryPort, uow: UnitOfWorkPort):
        self.user_repo = user_repo
        self.uow = uow

    async def execute(
        self,
        email: str,
        code_expiration_time: int,
        link: str,
        deadline: int,
    ):
        """Generates a code and persists an email verification message.

        Args:
            email (str):
                User email address used to identify the account.
            code_expiration_time (int):
                Verification code expiration time in minutes.
            link (str):
                Frontend link that redirects the user to the email
                verification screen where the verification code
                must be entered.
            deadline (int):
                Maximum number of days allowed for the user to
                verify the email address before account expiration.

        Raises:
            UserNotFoundError:
                - If no user exists with the provided email.
            EmailAlreadyVerifiedError:
                - If user's email is already verified.
            InactiveUserError:
                - If user account is inactive.
            InfrastructureError:
                - If persistence or registration fails.
        """
        user: User | None = await self.user_repo.get_by_email(email)

        if user is None:
            raise UserNotFoundError()

        if user.email_verified:
            raise EmailAlreadyVerifiedError()

        if not user.is_active:
            raise InactiveUserError()

        # When creating a new verification code, it should start as not sent.
        verification_code: VerificationCode = new_email_verification_code(
            user_public_id=user.public_id,
            code=Code.generate(),
            created_at=datetime.now(timezone.utc),
            expires_at=(
                datetime.now(timezone.utc)
                + timedelta(minutes=code_expiration_time)
            ),
            sent_at=None,
        )

        payload = EmailVerificationPayload(
            to=user.email.value,
            code=verification_code.code.value,
            expiration=str(code_expiration_time),
            link=link,
            deadline=str(deadline),
        )

        message = Message(
            type=MessageType.SEND_EMAIL_VERIFICATION_CODE,
            payload=payload,
        )

        # The verification code and message are persisted,
        # in an atomic transaction.
        async with self.uow:
            await self.uow.code_repo.create(verification_code)
            await self.uow.message_repo.create(message)
