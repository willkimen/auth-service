from dataclasses import dataclass
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import EmailVerifiedPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    MessageRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.email_verification import (
    EmailVerificationUseCase,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    DomainError,
    EmailAlreadyVerifiedError,
    InactiveUserError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)

# args para use_case.execute()
subject = 'Email verified successfully'


async def test_email_verified_successfully(
    unverified_user: User,
    create_unused_code,
):
    """
    Test if the email verification flow is correctly executed.
    The code must be unused, and the user must not be verified yet.
    """
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(unverified_user, unused_code)
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act
    await use_case.execute(
        unverified_user.email.value,
        unused_code.code.value,
    )

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once_with(
        unverified_user.email.value
    )
    mocks.code_repo.get_by_user_id_and_code.assert_called_once_with(
        unverified_user.public_id, unused_code.code.value
    )
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.message_repo.create.assert_called_once()

    # assert that user_repo.update() was called with correct arguments
    user_arg: User = mocks.uow.user_repo.update.call_args[0][0]
    assert user_arg.public_id == unverified_user.public_id
    assert user_arg.email.value == unverified_user.email.value
    assert user_arg.hash_password.value == unverified_user.hash_password.value
    assert user_arg.created_at == unverified_user.created_at
    assert user_arg.email_verified is True
    assert user_arg.is_active is True
    assert user_arg.last_login_at is None
    assert user_arg.updated_at == unverified_user.updated_at

    # assert that code_repo.update() was called with correct arguments
    code_arg: VerificationCode = mocks.uow.code_repo.update.call_args[0][0]
    assert code_arg.code == unused_code.code
    assert code_arg.user_public_id == unused_code.user_public_id
    assert code_arg.payload is None
    assert code_arg.created_at == unused_code.created_at
    assert code_arg.expires_at == unused_code.expires_at
    assert code_arg.used_at == unused_code.used_at
    assert isinstance(code_arg.used_at, datetime)
    assert code_arg.type == unused_code.type

    # assert that message.create() was called with correct arguments
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.id is not None
    assert message_arg.type == MessageType.NOTIFICATION_EMAIL_VERIFIED

    payload: EmailVerifiedPayload = message_arg.payload
    assert payload.to == user_arg.email.value
    assert payload.subject == 'Email verified successfully'


async def test_verification_fails_when_user_does_not_exist(
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(None, unused_code)
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_user_already_verified(
    verified_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(verified_user, unused_code)
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(EmailAlreadyVerifiedError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_user_inactive(
    inactive_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(inactive_user, unused_code)
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_get_user_fails(
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to return a user from the repository.
    """
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(None, unused_code)
    mocks.user_repo.get_by_email.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_user_state_is_corrupted(
    create_unused_code,
):
    """
    The returned user instance may raise a domain error when built in
    the repository layer. Test if this error propagates to the use
    case, aborting the verification flow.
    """
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(None, unused_code)
    mocks.user_repo.get_by_email.side_effect = CorruptedPersistenceStateError(
        DomainError('some domain error')
    )
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_does_not_exist(
    unverified_user: User,
):
    mocks: DependeciesMocked = mocks_factory(unverified_user, None)
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and arrange
    with pytest.raises(VerificationCodeNotFoundError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_already_used(
    unverified_user: User,
    create_used_code,
):
    used_code = create_used_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(unverified_user, used_code)
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(VerificationCodeAlreadyUsedError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_expired(
    unverified_user: User,
    create_expired_code,
):
    expired_code = create_expired_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(unverified_user, expired_code)
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(VerificationCodeExpiredError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_type_is_invalid(
    unverified_user: User,
    create_unused_code,
):
    code_incorrect_type = create_unused_code(CodeType.CHANGE_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        unverified_user,
        code_incorrect_type,
    )
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(VerificationCodeTypeError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_get_code_fails(unverified_user: User):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to return a verification code from the repository.
    """
    mocks: DependeciesMocked = mocks_factory(unverified_user, None)
    mocks.code_repo.get_by_user_id_and_code.side_effect = InfrastructureError(
        'Error attempting to get code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act anda assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_veritication_code_state_is_corrupted(
    unverified_user: User,
):
    """
    The returned verification code instance may raise a domain error
    when built in the repository layer. Test if this error propagates
    to the use case, aborting the verification flow.
    """
    mocks: DependeciesMocked = mocks_factory(unverified_user, None)
    mocks.code_repo.get_by_user_id_and_code.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act anda assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_persist_user_update_fails(
    unverified_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist an user in the repository.
    """
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(unverified_user, unused_code)
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )
    mocks.uow.user_repo.update.side_effect = InfrastructureError(
        'Error attempting to update user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()

    # assert was not called
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_persist_code_update_fails(
    unverified_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a verification code in the repository.
    """
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(unverified_user, unused_code)
    mocks.uow.code_repo.update.side_effect = InfrastructureError(
        'Error attempting to update code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_message_persists_fails(
    unverified_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a message in the repository.
    """
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(unverified_user, unused_code)
    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist message',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was not called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.message_repo.create.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies for the email
    verification confirmation flow.
    """

    user_repo: AsyncMock
    code_repo: AsyncMock
    uow: AsyncMock


def mocks_factory(
    user: User | None,
    verification_code: VerificationCode | None,
) -> DependeciesMocked:
    """
    Create and configure mocked repositories and unit of work
    dependencies for the email verification use case.

    The provided user and verification code instances simulate
    persisted entities returned by repository queries during the
    execution flow.
    """
    user_repo = AsyncMock(spec=UserRepositoryPort)
    user_repo.get_by_email.return_value = user

    code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    code_repo.get_by_user_id_and_code.return_value = verification_code

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.user_repo.update.return_value = None

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.update.return_value = None

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    return DependeciesMocked(user_repo, code_repo, uow)
