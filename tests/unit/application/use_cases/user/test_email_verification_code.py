from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    UserNotFoundError,
)
from application.messages.email_payloads import EmailVerificationPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    MessageRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.email_verification_code import (
    EmailVerificationCodeUseCase,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    DomainError,
    EmailAlreadyVerifiedError,
    InactiveUserError,
)
from domain.value_objects.code import Code

code_expiration_time = 15
deadline = 7


async def test_initialize_email_verification_process_successfully(
    unverified_user: User,
):
    """
    Test if the complete flow initializing email verification runs
    successfully.

    Success is verified by checking if key methods are called with
    the correct arguments.

    args:
        unverified_user (User): A user with an unverified state.
                        It must be unverified because it will be
                        used in mocks.

    """
    mocks: DependeciesMocked = mocks_factory(unverified_user)
    use_case = EmailVerificationCodeUseCase(mocks.uow)

    # act
    await use_case.execute(
        unverified_user.email.value, code_expiration_time, deadline
    )

    # Assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once_with(
        unverified_user.email.value
    )
    mocks.uow.code_repo.create.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited()
    mocks.uow.__aenter__.assert_awaited()
    mocks.uow.__aexit__.assert_awaited()

    # Assert that code_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a VerificationCode instance, which must
    # contain the following state:
    code_arg: VerificationCode = mocks.uow.code_repo.create.call_args[0][0]
    assert code_arg.user_public_id == unverified_user.public_id
    assert code_arg.used_at is None
    assert code_arg.expires_at > code_arg.created_at
    assert code_arg.payload is None
    assert code_arg.type is CodeType.EMAIL_VERIFICATION

    code: Code = code_arg.code
    assert isinstance(code.value, str)
    number_digits = 6
    assert len(code.value) == number_digits
    assert code.value.isdigit()

    # Assert that message_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a Message instance, which must
    # contain the following state:
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.type == MessageType.EMAIL_VERIFICATION_CODE

    payload: EmailVerificationPayload = message_arg.payload
    assert payload.to == unverified_user.email.value
    assert payload.expiration == str(code_expiration_time)
    assert payload.deadline == str(deadline)
    assert payload.code == code_arg.code.value
    assert payload.subject == 'Verify your email'


async def test_user_must_exist():
    """
    The initial verification process is aborted if the user does
    not exist.
    """
    mocks: DependeciesMocked = mocks_factory(None)
    use_case = EmailVerificationCodeUseCase(mocks.uow)

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute('', 0, 0)

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_already_verified_user_cannot_perform_verification_again(
    verified_user: User,
):
    """
    The initial verification process is aborted if the user is
    already verified.
    """
    mocks: DependeciesMocked = mocks_factory(verified_user)
    use_case = EmailVerificationCodeUseCase(mocks.uow)

    # act and assert
    with pytest.raises(EmailAlreadyVerifiedError):
        await use_case.execute('', 0, 0)

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_inactive_users_cannot_initiate_verification_process(
    inactive_user: User,
):
    """
    The initial verification process is aborted if the user is
    inactive. Only active users can verify their email.
    """
    mocks: DependeciesMocked = mocks_factory(inactive_user)
    use_case = EmailVerificationCodeUseCase(mocks.uow)

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute('', 0, 0)

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_verification_process_not_initialize_when_get_user_fails(
    unverified_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to fetch a user from the repository.
    """
    mocks: DependeciesMocked = mocks_factory(unverified_user)
    mocks.uow.user_repo.get_by_email.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = EmailVerificationCodeUseCase(mocks.uow)

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', 0, 0)

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_verification_process_not_initialize_when_user_state_corrupted(
    unverified_user: User,
):
    """
    The returned user instance may raise a domain error when built in
    the repository layer. Test if this error propagates to the use
    case, aborting the verification flow.
    """
    mocks: DependeciesMocked = mocks_factory(unverified_user)
    mocks.uow.user_repo.get_by_email.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )
    use_case = EmailVerificationCodeUseCase(mocks.uow)

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute('', 0, 0)

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_verification_process_not_initialize_when_persists_code_fails(
    unverified_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a verification code in the repository.
    """
    mocks: DependeciesMocked = mocks_factory(unverified_user)
    mocks.uow.code_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = EmailVerificationCodeUseCase(mocks.uow)

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', 0, 0)

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()
    mocks.uow.__aenter__.assert_awaited()
    mocks.uow.__aexit__.assert_awaited()
    mocks.uow.code_repo.create.assert_awaited()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_verification_process_not_initialize_when_message_persits_fails(
    unverified_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a message in the repository.
    """
    mocks: DependeciesMocked = mocks_factory(unverified_user)
    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = EmailVerificationCodeUseCase(mocks.uow)

    # act and arrange
    with pytest.raises(InfrastructureError):
        await use_case.execute('', 0, 0)

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited()
    mocks.uow.__aenter__.assert_awaited()
    mocks.uow.__aexit__.assert_awaited()
    mocks.uow.code_repo.create.assert_awaited()
    mocks.uow.message_repo.create.assert_awaited()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies for the email
    verification use case.
    """

    uow: AsyncMock


def mocks_factory(user: User | None) -> DependeciesMocked:
    """
    Create mocked dependencies for the email verification code use case.

    The configured mocks simulate repository lookups and transactional
    persistence operations used during the verification code generation flow.
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
