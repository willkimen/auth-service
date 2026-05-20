from dataclasses import dataclass
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    PasswordMismatchError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import PasswordResetPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    HasherPort,
    MessageRepositoryPort,
    TokenRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.reset_password import ResetPasswordUseCase
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    DomainError,
    InactiveUserError,
    InvalidPasswordError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)


async def test_password_reset_successfully(
    active_user: User,
    create_unused_code,
):
    """
    Test if the password reset flow is correctly executed.

    The user must be active and the verification code must be unused
    and valid.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    hashed_password = 'new-password-hashed'

    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        hashed_password,
    )

    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    raw_password = 'Password123@'
    raw_password_confirmation = 'Password123@'

    # act
    await use_case.execute(
        active_user.email.value,
        unused_code.code.value,
        raw_password,
        raw_password_confirmation,
    )

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once_with(
        active_user.email.value
    )
    mocks.hasher.hash.assert_called_once_with(raw_password)
    mocks.code_repo.get_by_user_id_and_code.assert_called_once_with(
        active_user.public_id,
        unused_code.code.value,
    )
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.token_repo.revoke_all_refreshes.assert_called_once_with(
        active_user.public_id
    )
    mocks.uow.message_repo.create.assert_called_once()

    # assert that user_repo.update()
    # was called with the correct expected arguments.
    # The expected argument is a User instance with the password
    # updated using the hashed password returned by the hasher.
    user_arg: User = mocks.uow.user_repo.update.call_args[0][0]
    assert user_arg.public_id == active_user.public_id
    assert user_arg.email.value == active_user.email.value
    assert user_arg.hash_password.value == hashed_password
    assert user_arg.email_verified == active_user.email_verified
    assert user_arg.is_active == active_user.is_active
    assert user_arg.created_at == active_user.created_at
    assert user_arg.last_login_at == active_user.last_login_at
    assert isinstance(user_arg.updated_at, datetime)

    # assert that code_repo.update()
    # was called with the correct expected arguments.
    # The expected argument is a VerificationCode instance marked
    # as used during the password reset process.
    code_arg: VerificationCode = mocks.uow.code_repo.update.call_args[0][0]
    assert code_arg.code == unused_code.code
    assert code_arg.user_public_id == unused_code.user_public_id
    assert code_arg.type == unused_code.type
    assert code_arg.created_at == unused_code.created_at
    assert code_arg.expires_at == unused_code.expires_at
    assert code_arg.sent_at == unused_code.sent_at
    assert code_arg.payload == unused_code.payload
    assert isinstance(code_arg.used_at, datetime)

    # assert that message_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a Message instance notifying the
    # user that the password was successfully reset.
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.id is not None
    assert message_arg.type == MessageType.NOTIFICATION_PASSWORD_RESET

    payload: PasswordResetPayload = message_arg.payload
    assert payload.to == active_user.email.value
    assert payload.subject == 'Your password has been reset'


async def test_reset_password_fails_when_password_invalid(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when the provided password
    does not satisfy the password policy.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidPasswordError):
        await use_case.execute('', '', '', '')

    # assert was not called
    mocks.user_repo.get_by_email.assert_not_called()
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.hasher.hash.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_passwords_do_not_match(
    active_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    valid_password = 'Password12345!'

    # act and assert
    with pytest.raises(PasswordMismatchError):
        await use_case.execute(
            '',
            '',
            valid_password,
            'another-password',
        )

    # assert was not called
    mocks.user_repo.get_by_email.assert_not_called()
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.hasher.hash.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_user_does_not_exist(
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        None,
        unused_code,
        'hashed-password',
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.hasher.hash.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_get_user_fails(
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to return a user from the repository.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        None,
        unused_code,
        'hashed-password',
    )
    mocks.user_repo.get_by_email.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.hasher.hash.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_user_state_is_corrupted(
    create_unused_code,
):
    """
    The returned user instance may raise a domain error when built in
    the repository layer. Test if this error propagates to the use
    case, aborting the password reset flow.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        None,
        unused_code,
        'hashed-password',
    )
    mocks.user_repo.get_by_email.side_effect = CorruptedPersistenceStateError(
        DomainError('some domain error')
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.hasher.hash.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_user_inactive(
    inactive_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        inactive_user,
        unused_code,
        'hashed-password',
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.hasher.hash.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_hash_password_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to hash the password.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    mocks.hasher.hash.side_effect = InfrastructureError(
        'Error attempting to hash password',
        InfrastructureErrorCode.UNKNOWN,
        Exception(),
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_get_code_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to return a verification code from the repository.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    mocks.code_repo.get_by_user_id_and_code.side_effect = InfrastructureError(
        'Error attempting to get code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_verification_code_state_is_corrupted(
    active_user: User,
    create_unused_code,
):
    """
    The returned verification code instance may raise a domain error
    when built in the repository layer. Test if this error propagates
    to the use case, aborting the password reset flow.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    mocks.code_repo.get_by_user_id_and_code.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_code_does_not_exist(
    active_user: User,
):
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        None,
        'hashed-password',
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(VerificationCodeNotFoundError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_code_already_used(
    active_user: User,
    create_used_code,
):
    used_code = create_used_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        used_code,
        'hashed-password',
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(VerificationCodeAlreadyUsedError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_code_expired(
    active_user: User,
    create_expired_code,
):
    expired_code = create_expired_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        expired_code,
        'hashed-password',
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(VerificationCodeExpiredError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_code_type_is_invalid(
    active_user: User,
    create_unused_code,
):
    invalid_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        invalid_code,
        'hashed-password',
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(VerificationCodeTypeError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_reset_password_fails_when_persist_user_update_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist an user in the repository.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    mocks.uow.user_repo.update.side_effect = InfrastructureError(
        'Error attempting to update user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()

    # assert was not called
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_reset_password_fails_when_persist_code_update_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a verification code in the repository.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    mocks.uow.code_repo.update.side_effect = InfrastructureError(
        'Error attempting to update verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_reset_password_fails_when_revoke_tokens_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to revoke user refresh tokens.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    mocks.uow.token_repo.revoke_all_refreshes.side_effect = (
        InfrastructureError(
            'Error attempting to revoke refresh tokens',
            InfrastructureErrorCode.DATABASE,
            Exception(),
        )
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.token_repo.revoke_all_refreshes.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_called()


async def test_reset_password_fails_when_message_persist_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a message in the repository.
    """
    unused_code = create_unused_code(CodeType.RESET_PASSWORD)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
        'hashed-password',
    )
    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist message',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = ResetPasswordUseCase(
        mocks.user_repo,
        mocks.code_repo,
        mocks.hasher,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', 'Password12345!', 'Password12345!')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.hasher.hash.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.token_repo.revoke_all_refreshes.assert_called_once()
    mocks.uow.message_repo.create.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies used by the
    reset password use case tests.
    """

    user_repo: AsyncMock
    code_repo: AsyncMock
    hasher: AsyncMock
    uow: AsyncMock


def mocks_factory(
    user: User | None,
    verification_code: VerificationCode | None,
    hashed_password: str,
) -> DependeciesMocked:
    """
    Create and configure mocked repositories, hasher, and unit of
    work dependencies for the reset password use case.

    The provided user and verification code instances simulate
    persisted entities returned by repository queries during the
    execution flow.

    The provided hashed password simulates the value returned by the
    hasher after processing the raw password informed by the user.
    """
    user_repo = AsyncMock(spec=UserRepositoryPort)
    user_repo.get_by_email.return_value = user

    code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    code_repo.get_by_user_id_and_code.return_value = verification_code

    hasher = AsyncMock(spec=HasherPort)
    hasher.hash.return_value = hashed_password

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.user_repo.update.return_value = None

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.update.return_value = None

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    uow.token_repo = AsyncMock(spec=TokenRepositoryPort)
    uow.token_repo.revoke_all_refreshes.return_value = None

    return DependeciesMocked(user_repo, code_repo, hasher, uow)
