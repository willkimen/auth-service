from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    UserNotFoundError,
)
from application.messages.email_payloads import ResetPasswordPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    MessageRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.reset_password_code import (
    ResetPasswordCodeUseCase,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.exceptions import DomainError, InactiveUserError

email = 'email@email.com'
code_expiration_time = 15


async def test_initialize_reset_password_process_successfully(
    active_user: User,
):
    """
    Test if the complete password reset initialization flow runs
    successfully.

    Success is verified by checking if key methods are called with
    the correct arguments and expected state transitions.

    Args:
        active_user (User):
            Active persisted user used during the password reset flow.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    use_case = ResetPasswordCodeUseCase(mocks.uow)

    # act
    await use_case.execute(
        email,
        code_expiration_time,
    )

    # Assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once_with(email)
    mocks.uow.code_repo.create.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # Assert that code_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a VerificationCode instance, which must
    # contain the following state:
    code_arg: VerificationCode = mocks.uow.code_repo.create.call_args[0][0]

    assert code_arg.code is not None
    assert code_arg.user_public_id == active_user.public_id
    assert code_arg.expires_at > code_arg.created_at
    assert code_arg.payload is None
    assert code_arg.used_at is None

    # Assert that message_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a Message instance, which must
    # contain the following state:
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]

    assert message_arg.id is not None
    assert message_arg.type == MessageType.PASSWORD_RESET_CODE
    assert message_arg.expires_at == code_arg.expires_at

    payload: ResetPasswordPayload = message_arg.payload

    assert payload.to == email
    assert payload.code == code_arg.code.value
    assert payload.expiration == str(code_expiration_time)
    assert payload.subject == 'Reset your password'


async def test_user_must_exist():
    mocks: DependeciesMocked = mocks_factory(None)
    use_case = ResetPasswordCodeUseCase(mocks.uow)

    # act
    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            email,
            code_expiration_time,
        )

    # Assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()

    # Assert was not called
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_reset_process_not_initialize_when_user_state_corrupted(
    active_user: User,
):
    """
    The returned user instance may raise a domain error when built in
    the repository layer. Test if this error propagates to the use
    case, aborting the verification flow.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.user_repo.get_by_email.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )
    use_case = ResetPasswordCodeUseCase(mocks.uow)

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(
            email,
            code_expiration_time,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()

    # Assert was not called
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_reset_process_not_initialize_when_get_user_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to fetch a user from the repository.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.user_repo.get_by_email.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )
    use_case = ResetPasswordCodeUseCase(mocks.uow)

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email,
            code_expiration_time,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()

    # Assert was not called
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_inactive_users_cannot_initiate_reset_process(inactive_user):
    mocks: DependeciesMocked = mocks_factory(inactive_user)
    use_case = ResetPasswordCodeUseCase(mocks.uow)

    # act
    with pytest.raises(InactiveUserError):
        await use_case.execute(
            email,
            code_expiration_time,
        )

    # Assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once_with(email)

    # Assert was not called
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_reset_process_not_initialize_when_code_persits_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a code in the repository.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.code_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )
    use_case = ResetPasswordCodeUseCase(mocks.uow)

    # act
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email,
            code_expiration_time,
        )

    # Assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once_with(email)
    mocks.uow.code_repo.create.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_reset_process_not_initialize_when_message_persits_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a message in the repository.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist message',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )
    use_case = ResetPasswordCodeUseCase(mocks.uow)

    # act
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email,
            code_expiration_time,
        )

    # Assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once_with(email)
    mocks.uow.code_repo.create.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()


@dataclass(frozen=True)
class DependeciesMocked:
    uow: AsyncMock


def mocks_factory(user: User | None) -> DependeciesMocked:
    """
    Create mocked dependencies for the password reset code use case.

    The configured mocks simulate persisted user retrieval and
    transactional persistence operations used during the password
    reset initialization flow.
    """

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    # Simulate a persisted user returned by repository lookup.
    uow.user_repo.get_by_email.return_value = user

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.create.return_value = None

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    return DependeciesMocked(uow)
