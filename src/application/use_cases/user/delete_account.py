from datetime import datetime, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import AccountDeletedPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
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


class DeleteUseCase:
    """
    Handles the authenticated account deletion workflow.

    This use case validates the authentication token, verifies token
    existence and revocation status, loads and validates the user,
    checks the provided verification code, ensures it matches the
    DELETE_ACCOUNT flow, enforces expiration and single-use rules,
    performs the account deletion inside a transactional boundary,
    revokes all refresh tokens, deletes verification codes, and
    persists a notification message informing the user about account
    deletion.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation and decoding.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        self.token_manager = token_manager
        self.uow = uow

    async def execute(self, access: str, code: str):
        """
        Executes the authenticated account deletion flow.

        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code` (str):
                - Verification code authorizing account deletion.

        Raises:
            `InvalidTokenError`:
                - If token validation fails at domain level.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `InfrastructureError`:
                - If token decoding, persistence, or transactional
                  operations fail unexpectedly.
            `TokenNotFoundError`:
                - If token does not exist in persistence.
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
                - If verification code is not DELETE_ACCOUNT type.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
        """
        token_payload: PayloadTokenDTO = self.token_manager.validate(access)

        if token_payload.typ != 'access':
            raise InvalidTokenTypeError()

        if not await self.uow.token_repo.exists(token_payload.jti):
            raise TokenNotFoundError()

        if await self.uow.token_repo.is_revoked(token_payload.jti):
            raise TokenRevokedError()

        user: User | None = await self.uow.user_repo.get_by_public_id(
            token_payload.sub
        )

        if user is None:
            raise UserNotFoundError()

        if not user.is_active:
            raise InactiveUserError()

        verification_code: (
            VerificationCode | None
        ) = await self.uow.code_repo.get_by_user_id_and_code(
            user.public_id, code
        )

        if verification_code is None:
            raise VerificationCodeNotFoundError()

        if verification_code.is_used():
            raise VerificationCodeAlreadyUsedError()

        if not verification_code.type == CodeType.DELETE_ACCOUNT:
            raise VerificationCodeTypeError()

        if verification_code.is_expired(datetime.now(timezone.utc)):
            raise VerificationCodeExpiredError()

        verification_code.mark_as_used(datetime.now(timezone.utc))

        message = Message(
            type=MessageType.NOTIFICATION_DELETED,
            payload=AccountDeletedPayload(to=user.email.value),
        )

        # Persist related changes atomically as a single unit of work.
        async with self.uow:
            await self.uow.user_repo.delete(user.public_id)
            await self.uow.code_repo.delete_all(user.public_id)
            await self.uow.token_repo.revoke_all(user.public_id)
            await self.uow.message_repo.create(message)
