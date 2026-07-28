from datetime import datetime, timedelta, timezone

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InvalidTokenTypeError,
    UserNotFoundError,
)
from application.messages.email_payloads import EmailCodePayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.entities.verification_code_factory import new_change_password_code
from domain.exceptions import InactiveUserError
from domain.value_objects.code import Code


class ChangePasswordCodeUseCase:
    """
    Initiates the password change verification process for an
    authenticated user by generating a temporary verification code
    for the password change operation.

    The verification code acts as a temporary credential that can
    later be used to authorize the completion of the password change.
    The code and the data required to deliver it to the user are
    persisted for subsequent processing.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the password change
              verification process.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        self.token_manager = token_manager
        self.uow = uow

    async def execute(self, access: str, code_expiraton_time: int):
        """
        Initiates the password change verification process by
        generating a temporary verification code for the
        authenticated user.

        The authenticated user must exist and have an active account.
        A verification code with a limited validity period is then
        generated and persisted together with the data required to
        deliver the code to the user.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting the password change.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

        Raises:
            `InvalidTokenError`:
                - Raised when the provided token is invalid, expired,
                  malformed, or contains invalid claims.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `UserNotFoundError`:
                - Raised when the authenticated user no longer exists.
            `InactiveUserError`:
                - Raised when the authenticated user is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted user data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - Raised when persistence operations, token operations,
                  transaction handling, or external infrastructure services
                  fail unexpectedly.
        """

        async with self.uow:
            token_payload: PayloadTokenDTO = self.token_manager.validate(
                access
            )

            if token_payload.typ != 'access':
                raise InvalidTokenTypeError()

            user: User | None = await self.uow.users.get_by_public_id(
                token_payload.sub
            )

            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise InactiveUserError()

            verification_code: VerificationCode = new_change_password_code(
                user_public_id=user.public_id,
                code=Code.generate(),
                created_at=datetime.now(timezone.utc),
                expires_at=(
                    datetime.now(timezone.utc)
                    + timedelta(minutes=code_expiraton_time)
                ),
            )

            payload = EmailCodePayload(
                to=user.email.value,
                code=verification_code.code.value,
            )

            message = Message(
                type=MessageType.CHANGE_PASSWORD_CODE,
                payload=payload,
                expires_at=verification_code.expires_at,
            )

            await self.uow.codes.create(verification_code)
            await self.uow.messages.create(message)
