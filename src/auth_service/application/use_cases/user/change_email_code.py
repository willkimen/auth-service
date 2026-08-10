from datetime import datetime, timedelta, timezone

from auth_service.application.dtos.token_dto import PayloadTokenDTO
from auth_service.application.exceptions import (
    InvalidTokenTypeError,
    UserNotFoundError,
)
from auth_service.application.messages.email_payloads import EmailCodePayload
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_types import MessageType
from auth_service.application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
)
from auth_service.domain.entities.user import User
from auth_service.domain.entities.verification_code import VerificationCode
from auth_service.domain.entities.verification_code_factory import (
    new_change_email_code,
)
from auth_service.domain.exceptions import InactiveUserError
from auth_service.domain.value_objects.code import Code
from auth_service.domain.value_objects.email import Email


class ChangeEmailCodeUseCase:
    """
    Initiates the email change verification process for an
    authenticated user by generating a temporary verification code
    for the requested new email address.

    The verification code acts as a temporary credential that can
    later be used to authorize the completion of the email change.
    The code and the data required to deliver it to the new email
    address are persisted for subsequent processing.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the email change
              verification process.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ):
        self.token_manager = token_manager
        self.uow = uow

    async def execute(
        self,
        access: str,
        new_email: str,
        code_expiration_time: int,
    ):
        """
        Initiates the email change verification process by generating
        a temporary verification code for the authenticated user's
        requested new email address.

        The requested email address must be valid, and the authenticated
        user must exist and be active. A verification code with a
        limited validity period is then generated and persisted
        together with the data required to deliver the code to the
        requested email address.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting the email change.
            `new_email` (str):
                - New email address requested by the authenticated
                  user.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

        Raises:
            `InvalidEmailError`:
                - Raised when the provided email is invalid.
            `InvalidTokenError`:
                - Raised when token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `UserNotFoundError`:
                - Raised when no user exists for the authenticated token.
            `InactiveUserError`:
                - Raised when the authenticated user is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - Raised when an unexpected infrastructure failure occurs
                  within an output adapter.
        """

        async with self.uow:
            email_vo = Email(new_email)

            token_payload: PayloadTokenDTO = self.token_manager.validate(access)

            if token_payload.typ != 'access':
                raise InvalidTokenTypeError()

            user: User | None = await self.uow.users.get_by_public_id(token_payload.sub)

            if user is None:
                raise UserNotFoundError()

            if not user.is_active:
                raise InactiveUserError()

            verification_code: VerificationCode | None = new_change_email_code(
                user_public_id=user.public_id,
                code=Code.generate(),
                created_at=datetime.now(timezone.utc),
                expires_at=(
                    datetime.now(timezone.utc) + timedelta(minutes=code_expiration_time)
                ),
                new_email=email_vo.value,
            )

            message = Message(
                type=MessageType.CHANGE_EMAIL_CODE,
                payload=EmailCodePayload(
                    to=email_vo.value,
                    code=verification_code.code.value,
                ),
                expires_at=verification_code.expires_at,
            )

            await self.uow.codes.create(verification_code)
            await self.uow.messages.create(message)
