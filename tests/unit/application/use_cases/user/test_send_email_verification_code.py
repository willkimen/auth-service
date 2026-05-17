from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
    UserNotFoundError,
)
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    MessageRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.send_email_verification_code import (
    SendEmailVerificationCodeUseCase,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import EmailAlreadyVerifiedError, InactiveUserError

code_expiration_time = 15
link = 'www.test.com/send-code'
deadline = 7


async def test_initialize_email_verification_process_successfully(
    unverified_user: User,
):
    # arrange
    mocks = mocks_factory(unverified_user)

    use_case = SendEmailVerificationCodeUseCase(mocks.user_repo, mocks.uow)

    # act
    await use_case.execute(
        unverified_user.email.value, code_expiration_time, link, deadline
    )

    # Assert was called
    mocks.user_repo.get_by_email.assert_called_once_with(
        unverified_user.email.value
    )
    mocks.uow.code_repo.create.assert_called_once()
    mocks.uow.message_repo.create.assert_called()
    mocks.uow.__aenter__.assert_called()
    mocks.uow.__aexit__.assert_called()

    # Assert that code_repo.create()
    # was called with the correct expected arguments.
    code_arg: VerificationCode = mocks.uow.code_repo.create.call_args[0][0]
    assert code_arg.user_public_id == unverified_user.public_id
    assert code_arg.used_at is None
    assert code_arg.sent_at is None

    code = code_arg.code
    assert isinstance(code.value, str)
    number_digits = 6
    assert len(code.value) == number_digits
    assert code.value.isdigit()

    assert code_arg.expires_at > code_arg.created_at
    assert code_arg.payload is None
    assert code_arg.type is CodeType.EMAIL_VERIFICATION

    # Assert that message_repo.create()
    # was called with the correct expected arguments.
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.type == MessageType.SEND_EMAIL_VERIFICATION_CODE
    payload: dict = message_arg.payload.to_dict()
    assert payload['to'] == unverified_user.email.value
    assert payload['link'] == str(link)
    assert payload['expiration'] == f'{code_expiration_time} minutes'
    assert payload['deadline'] == f'{deadline} days'
    assert payload['code'] == code_arg.code.value
    assert payload['subject'] == 'Verify your email'


async def test_verification_process_not_initialize_when_user_not_found():
    # arrange
    mocks = mocks_factory(None)

    use_case = SendEmailVerificationCodeUseCase(mocks.user_repo, mocks.uow)

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute('', 0, '', 0)

    # assert was called
    mocks.user_repo.get_by_email.assert_called()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_process_not_initialize_when_user_already_verified(
    verified_user: User,
):
    # arrange
    mocks = mocks_factory(verified_user)

    use_case = SendEmailVerificationCodeUseCase(mocks.user_repo, mocks.uow)

    # act and assert
    with pytest.raises(EmailAlreadyVerifiedError):
        await use_case.execute('', 0, '', 0)

    # assert was called
    mocks.user_repo.get_by_email.assert_called()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_process_not_initialize_when_user_is_inactive(
    inactive_user: User,
):
    # arrange
    mocks = mocks_factory(inactive_user)

    use_case = SendEmailVerificationCodeUseCase(mocks.user_repo, mocks.uow)

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute('', 0, '', 0)

    # assert was called
    mocks.user_repo.get_by_email.assert_called()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_process_not_initialize_when_persists_code_fails(
    unverified_user: User,
):
    # arrange
    mocks = mocks_factory(unverified_user)

    mocks.uow.code_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = SendEmailVerificationCodeUseCase(mocks.user_repo, mocks.uow)

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', 0, '', 0)

    # assert was called
    mocks.user_repo.get_by_email.assert_called()
    mocks.uow.__aenter__.assert_called()
    mocks.uow.__aexit__.assert_called()
    mocks.uow.code_repo.create.assert_called()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_process_not_initialize_when_message_persits_fails(
    unverified_user: User,
):
    # arrange
    mocks = mocks_factory(unverified_user)

    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = SendEmailVerificationCodeUseCase(mocks.user_repo, mocks.uow)

    # act and arrange
    with pytest.raises(InfrastructureError):
        await use_case.execute('', 0, '', 0)

    # assert was called
    mocks.user_repo.get_by_email.assert_called()
    mocks.uow.__aenter__.assert_called()
    mocks.uow.__aexit__.assert_called()
    mocks.uow.code_repo.create.assert_called()
    mocks.uow.message_repo.create.assert_called()


@dataclass(frozen=True)
class DependeciesMocked:
    user_repo: AsyncMock
    uow: AsyncMock


def mocks_factory(user: User | None) -> DependeciesMocked:
    user_repo = AsyncMock(spec=UserRepositoryPort)
    user_repo.get_by_email.return_value = user

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.create.return_value = None

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    return DependeciesMocked(user_repo, uow)
