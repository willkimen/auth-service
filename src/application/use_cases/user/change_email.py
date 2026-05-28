from datetime import datetime, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import EmailChangedPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
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
from domain.value_objects.email import Email


class ChangeEmailUseCase:
    """
    Completes the user email change process using a previously
    generated verification code associated with an authenticated
    session.

    The use case validates the authenticated token, checks whether
    the token exists and is not revoked, validates the verification
    code state, updates the user's email address, revokes all active
    refresh tokens, and persists a notification message informing
    the user about the successful email change.

    Attributes:
        `user_repo` (UserRepositoryPort):
            - Port/Interface responsible for user data retrieval.
        `code_repo` (VerificationCodeRepositoryPort):
            - Port/Interface responsible for verification code
              retrieval and persistence.
        `token_repo` (TokenRepositoryPort):
            - Port/Interface responsible for token persistence
              and revocation checks.
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token validation and
              payload extraction.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        user_repo: UserRepositoryPort,
        code_repo: VerificationCodeRepositoryPort,
        token_repo: TokenRepositoryPort,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        self.user_repo = user_repo
        self.code_repo = code_repo
        self.token_repo = token_repo
        self.token_manager = token_manager
        self.uow = uow

    async def execute(self, access: str, code: str):
        """
        Changes the authenticated user's email address after
        validating a previously generated email change verification
        code.

        The flow validates the access token, verifies whether the
        token exists and is active, validates the verification code,
        updates the user's email address, revokes all active refresh
        tokens, and persists a notification message informing the
        user about the completed email change.

        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code` (str):
                - Verification code sent to the new email address.

        Raises:
            `InvalidTokenError`:
                - If the provided token is malformed, invalid,
                  expired, or cannot be decoded.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `TokenNotFoundError`:
                - If the token identifier does not exist in the
                  persistence layer.
            `TokenRevokedError`:
                - If the token has been revoked.
            `VerificationCodeNotFoundError`:
                - If no verification code exists for the user and
                  provided code.
            `VerificationCodeAlreadyUsedError`:
                - If the verification code was already used.
            `VerificationCodeTypeError`:
                - If the verification code type is invalid for the
                  email change operation.
            `VerificationCodeExpiredError`:
                - If the verification code has expired.
            `UserNotFoundError`:
                - If no user exists for the authenticated token.
            `InactiveUserError`:
                - If the user account is inactive.
            `InvalidEmailError`:
                - If the email extracted from the verification code
                  is invalid.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain entities or value objects.
            `InfrastructureError`:
                - If an unexpected failure occurs in the infrastructure
                  layer during repository, token, or persistence
                  operations.
        """
        token_payload: PayloadTokenDTO = self.token_manager.validate(access)

        if token_payload.typ != 'access':
            raise InvalidTokenTypeError()

        if not await self.token_repo.exists(token_payload.jti):
            raise TokenNotFoundError()

        if await self.token_repo.is_revoke(token_payload.jti):
            raise TokenRevokedError()

        verification_code: (
            VerificationCode | None
        ) = await self.code_repo.get_by_user_id_and_code(
            token_payload.sub, code
        )

        if verification_code is None:
            raise VerificationCodeNotFoundError()

        if verification_code.is_used():
            raise VerificationCodeAlreadyUsedError()

        if not verification_code.type == CodeType.CHANGE_EMAIL:
            raise VerificationCodeTypeError()

        if verification_code.is_expired(datetime.now(timezone.utc)):
            raise VerificationCodeExpiredError()

        verification_code.mark_as_used(datetime.now(timezone.utc))

        user: User | None = await self.user_repo.get_by_public_id(
            token_payload.sub
        )

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise InactiveUserError()

        new_email = verification_code.get_new_email()
        new_email_vo: Email = Email(new_email)
        user.change_email(new_email_vo)

        message = Message(
            type=MessageType.NOTIFICATION_EMAIL_CHANGED,
            payload=EmailChangedPayload(to=user.email.value),
        )

        async with self.uow:
            await self.uow.user_repo.update(user)
            await self.uow.code_repo.update(verification_code)
            await self.uow.message_repo.create(message)
            await self.uow.token_repo.revoke_all_refreshes(user.public_id)
