from datetime import datetime, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    PasswordMismatchError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import PasswordChangedPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    HasherPort,
    TokenManagerPort,
    TokenRepositoryPort,
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


class ChangePasswordUseCase:
    """
    Handles the authenticated password change workflow.

    This use case validates the new password against domain rules,
    confirms password confirmation consistency, validates the user's
    refresh token, verifies the authorization code, updates the user's
    password hash, revokes all active refresh tokens, and persists
    a notification message informing the user about the password change.

    Attributes:
        `user_repo` (UserRepositoryPort):
            - Repository responsible for user persistence operations.
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation.
        `code_repo` (VerificationCodeRepositoryPort):
            - Repository responsible for verification code persistence.
        `token_repo` (TokenRepositoryPort):
            - Repository responsible for refresh token persistence
              and revocation operations.
        `uow` (UnitOfWorkPort):
            - Transaction manager used to guarantee atomic persistence.
        `hasher` (HasherPort):
            - Service responsible for password hashing operations.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        token_manager: TokenManagerPort,
        code_repo: VerificationCodeRepositoryPort,
        token_repo: TokenRepositoryPort,
        uow: UnitOfWorkPort,
        hasher: HasherPort,
    ):
        self.user_repo = user_repo
        self.code_repo = code_repo
        self.token_manager = token_manager
        self.token_repo = token_repo
        self.uow = uow
        self.hasher = hasher

    async def execute(
        self,
        access: str,
        code: str,
        new_password: str,
        new_password_confirmation: str,
    ):
        """
        Executes the authenticated password change flow.

        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code` (str):
                - Verification code authorizing the password change.
            `new_password` (str):
                - New raw password provided by the user.
            `new_password_confirmation` (str):
                - Confirmation password used to validate consistency.

        Raises:
            `InvalidPasswordError`:
                - If password policy validation fails.
            `PasswordMismatchError`:
                - If password confirmation does not match.
            `InfrastructureError`:
                - If hashing, repositories, transactions,
                  or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `TokenNotFoundError`:
                - If token does not exist.
            `TokenRevokedError`:
                - If token has been revoked.
            `UserNotFoundError`:
                - If authenticated user cannot be found.
            `InactiveUserError`:
                - If authenticated user is inactive.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist.
            `VerificationCodeAlreadyUsedError`:
                - If verification code was already consumed.
            `VerificationCodeTypeError`:
                - If verification code type is invalid.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
        """
        PasswordPolicy.validate(new_password)

        if new_password != new_password_confirmation:
            raise PasswordMismatchError()

        hashed_password = self.hasher.hash(new_password)
        password_hash_vo = PasswordHash(hashed_password)

        token_payload: PayloadTokenDTO = self.token_manager.validate(access)

        if token_payload.typ != 'access':
            raise InvalidTokenTypeError()

        if not await self.token_repo.exists(token_payload.jti):
            raise TokenNotFoundError()

        if await self.token_repo.is_revoke(token_payload.jti):
            raise TokenRevokedError()

        user: User | None = await self.user_repo.get_by_public_id(
            token_payload.sub
        )

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise InactiveUserError()

        user.change_password(password_hash_vo)

        verification_code: (
            VerificationCode | None
        ) = await self.code_repo.get_by_user_id_and_code(user.public_id, code)

        if verification_code is None:
            raise VerificationCodeNotFoundError()

        if verification_code.is_used():
            raise VerificationCodeAlreadyUsedError()

        if not verification_code.type == CodeType.CHANGE_PASSWORD:
            raise VerificationCodeTypeError()

        if verification_code.is_expired(datetime.now(timezone.utc)):
            raise VerificationCodeExpiredError()

        verification_code.mark_as_used(datetime.now(timezone.utc))

        message = Message(
            type=MessageType.NOTIFICATION_PASSWORD_CHANGED,
            payload=PasswordChangedPayload(user.email.value),
        )

        async with self.uow:
            await self.uow.user_repo.update(user)
            await self.uow.code_repo.update(verification_code)
            await self.uow.token_repo.revoke_all_refreshes(user.public_id)
            await self.uow.message_repo.create(message)
