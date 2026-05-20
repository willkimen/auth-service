from datetime import datetime, timezone

from application.exceptions import (
    PasswordMismatchError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import PasswordResetPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    HasherPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
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
    Completes the password reset process for a user account.

    The use case validates the new password, verifies the reset code,
    updates the user's password, revokes all active refresh tokens,
    and persists a notification message informing the user that the
    password was successfully changed.

    Attributes:
        user_repo (UserRepositoryPort):
            - Port/Interface responsible for user data retrieval
              operations.
        code_repo (VerificationCodeRepositoryPort):
            - Port/Interface responsible for verification code
              retrieval operations.
        hasher (HasherPort):
            - Port/Interface responsible for securely hashing raw
              passwords.
        uow (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        code_repo: VerificationCodeRepositoryPort,
        hasher: HasherPort,
        uow: UnitOfWorkPort,
    ):
        self.user_repo = user_repo
        self.code_repo = code_repo
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
        Resets a user's password using a valid verification code.

        The flow validates the password policy, confirms password
        equality, retrieves the user and verification code, validates
        reset eligibility, updates the password, revokes all refresh
        tokens, and persists a notification message.

        Args:
            email (str):
                User email address associated with the account.
            code (str):
                Verification code informed by the user.
            raw_password (str):
                New raw password informed by the user.
            raw_password_confirmation (str):
                Confirmation password used to validate equality with
                the new password.

        Raises:
            InvalidPasswordError:
                - Raised when the password does not satisfy the
                  password policy.
            PasswordMismatchError:
                - Raised when password and confirmation password do
                  not match.
            UserNotFoundError:
                - If no user exists with the provided email.
            InactiveUserError:
                - If user account is inactive.
            VerificationCodeNotFoundError:
                - If verification code does not exist for the user
                  and code.
            VerificationCodeAlreadyUsedError:
                - If verification code was already used.
            VerificationCodeExpiredError:
                - If verification code has expired.
            VerificationCodeTypeError:
                - If verification code type is incorrect.
            CorruptedPersistenceStateError:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            InfrastructureError:
                - If an unexpected failure occurs within an output
                  adapter (infrastructure layer)
        """
        PasswordPolicy.validate(raw_password)

        if raw_password != raw_password_confirmation:
            raise PasswordMismatchError()

        # Retorna
        user: User | None = await self.user_repo.get_by_email(email)

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise InactiveUserError()

        password_hash_vo = PasswordHash(self.hasher.hash(raw_password))

        verification_code: (
            VerificationCode | None
        ) = await self.code_repo.get_by_user_id_and_code(user.public_id, code)

        if verification_code is None:
            raise VerificationCodeNotFoundError()

        if verification_code.is_used():
            raise VerificationCodeAlreadyUsedError()

        if verification_code.is_expired(datetime.now(timezone.utc)):
            raise VerificationCodeExpiredError()

        if not verification_code.type == CodeType.RESET_PASSWORD:
            raise VerificationCodeTypeError()

        verification_code.mark_as_used(datetime.now(timezone.utc))
        user.change_password(password_hash_vo)

        message = Message(
            type=MessageType.NOTIFICATION_PASSWORD_RESET,
            payload=PasswordResetPayload(user.email.value),
        )

        async with self.uow:
            await self.uow.user_repo.update(user)
            await self.uow.code_repo.update(verification_code)
            await self.uow.token_repo.revoke_all_refreshes(user.public_id)
            await self.uow.message_repo.create(message)
