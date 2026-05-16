from datetime import datetime, timezone

from application.dtos.verification_code_dto import (
    VerificationCodePersistenceDTO,
)
from application.exceptions import (
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import EmailVerifiedPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
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

    Retrieves the user and verification code, validates verification
    eligibility, marks the email as verified, marks the verification
    code as used, and persists a message to notify
    the user about successful email verification.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        code_repo: VerificationCodeRepositoryPort,
        uow: UnitOfWorkPort,
    ):
        self.user_repo = user_repo
        self.code_repo = code_repo
        self.uow = uow

    async def execute(self, email: str, code: str, login_link: str):
        """
        Verifies a user's email using a verification code and
        registers an asynchronous notification message.

        Args:
            email (str):
                User email address associated with the account.
            code (str):
                Verification code informed by the user.
            login_link (str):
                Frontend link that redirects the user to the login
                screen after successful email verification.

        Raises:
            UserNotFoundError:
                If no user exists with the provided email.
            VerificationCodeNotFoundError:
                If verification code does not exist for the user and code.
            EmailAlreadyVerifiedError:
                If user's email is already verified.
            InactiveUserError:
                If user account is inactive.
            VerificationCodeAlreadyUsedError:
                If verification code was already used.
            VerificationCodeExpiredError:
                If verification code has expired.
            VerificationCodeTypeError:
                If verification code type is incorrect.
            InfrastructureError:
                If persistence or registration fails.
        """
        user: User | None = await self.user_repo.get_by_email(email)

        if user is None:
            raise UserNotFoundError()

        if user.email_verified is True:
            raise EmailAlreadyVerifiedError()

        if user.is_active is False:
            raise InactiveUserError()

        code_persistence: (
            VerificationCodePersistenceDTO | None
        ) = await self.code_repo.get_by_user_id_and_code(
            user.public_id,
            code,
        )

        if code_persistence is None:
            raise VerificationCodeNotFoundError()

        verification_code: VerificationCode = code_persistence.to_entity()

        if verification_code.is_used():
            raise VerificationCodeAlreadyUsedError()

        if verification_code.is_expired(datetime.now(timezone.utc)):
            raise VerificationCodeExpiredError()

        if verification_code.type is not CodeType.EMAIL_VERIFICATION:
            raise VerificationCodeTypeError()

        user.mark_email_as_verified()
        verification_code.mark_as_used(datetime.now(timezone.utc))

        payload = EmailVerifiedPayload(user.email.value, link=login_link)

        message = Message(
            type=MessageType.SEND_NOTIFICATION_EMAIL_VERIFIED,
            payload=payload,
        )

        async with self.uow:
            await self.uow.user_repo.update(user)
            await self.uow.code_repo.update(
                VerificationCodePersistenceDTO.from_entity(verification_code)
            )
            await self.uow.message_repo.create(message)
