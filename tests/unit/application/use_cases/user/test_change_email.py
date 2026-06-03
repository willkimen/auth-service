import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import AsyncMock

import pytest

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidTokenError,
    InvalidTokenErrorCode,
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
    MessageRepositoryPort,
    RefreshTokenRepositoryPort,
    TokenManagerPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.change_email import ChangeEmailUseCase
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    DomainError,
    InactiveUserError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)

token = 'token-fake'
payload_new_email = {'new_email': 'email@email.com'}


async def test_email_changed_successfully(
    active_user: User,
    create_unused_code,
):
    """
    Test if the complete email change flow executes successfully.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
    )
    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act
    await use_case.execute(token, unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once_with(
        active_user.public_id,
        unused_code.code.value,
    )
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )

    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.code_repo.update.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()
    mocks.uow.token_repo.revoke_all.assert_awaited_once_with(
        active_user.public_id
    )

    # assert user persisted state
    user_arg: User = mocks.uow.user_repo.update.call_args[0][0]
    assert user_arg.public_id == active_user.public_id
    assert user_arg.email.value == (unused_code.get_new_email())
    assert user_arg.is_active is True

    # assert verification code persisted state
    code_arg: VerificationCode = mocks.uow.code_repo.update.call_args[0][0]
    assert code_arg.user_public_id == (unused_code.user_public_id)
    assert code_arg.user_public_id == (active_user.public_id)
    assert code_arg.type == CodeType.CHANGE_EMAIL
    assert code_arg.used_at is not None

    # assert message persisted state
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.type == MessageType.NOTIFICATION_EMAIL_CHANGED

    payload: EmailChangedPayload = message_arg.payload
    assert payload.to == user_arg.email.value
    assert payload.subject == 'Your email has been changed'


async def test_change_email_fails_when_token_invalid():
    mocks: DependeciesMocked = mocks_factory(None, None)
    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.EXPIRED
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_token_type_is_invalid():
    mocks: DependeciesMocked = mocks_factory(None, None)
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    mocks.token_manager.validate.return_value = PayloadTokenDTO(
        jti='jti',
        sub=uuid.uuid4(),
        exp=int(exp.timestamp()),
        typ='refresh',  # incorrect type
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_token_validate_fails():
    mocks: DependeciesMocked = mocks_factory(None, None)
    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error attempting to validate token',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_token_not_found():
    """
    The email change flow is aborted when the token does not exist.
    """
    mocks: DependeciesMocked = mocks_factory(None, None)
    mocks.uow.token_repo.exists.return_value = False

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenNotFoundError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_check_token_exists_fails():
    """
    Test if an exception is raised when an unexpected error occurs
    while checking token existence.
    """
    mocks: DependeciesMocked = mocks_factory(None, None)
    mocks.uow.token_repo.exists.side_effect = InfrastructureError(
        'Error attempting to check token existence',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_token_revoked():
    """
    The email change flow is aborted when the token was revoked.
    """
    mocks: DependeciesMocked = mocks_factory(None, None)
    mocks.uow.token_repo.is_revoked.return_value = True

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenRevokedError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()

    # assert was not called
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_check_token_revoke_fails():
    """
    Test if an exception is raised when an unexpected error occurs
    while checking token revoke state.
    """
    mocks: DependeciesMocked = mocks_factory(None, None)
    mocks.uow.token_repo.is_revoked.side_effect = InfrastructureError(
        'Error attempting to check token revoke state',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()

    # assert was not called
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_code_not_found(
    active_user: User,
):
    """
    The email change flow is aborted when the verification code
    does not exist.
    """
    mocks: DependeciesMocked = mocks_factory(active_user, None)

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(VerificationCodeNotFoundError):
        await use_case.execute('', '')

    # assert was called
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_code_already_used(
    active_user: User,
    create_used_code,
):
    used_code = create_used_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        used_code,
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(VerificationCodeAlreadyUsedError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_code_expired(
    active_user: User,
    create_expired_code,
):
    expired_code = create_expired_code(
        CodeType.CHANGE_EMAIL, payload_new_email
    )
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        expired_code,
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(VerificationCodeExpiredError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_code_type_invalid(
    active_user: User,
    create_unused_code,
):
    """
    The email change flow is aborted when the verification code
    type is invalid.
    """
    invalid_code = create_unused_code(
        CodeType.DELETE_ACCOUNT, payload_new_email
    )
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        invalid_code,
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(VerificationCodeTypeError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_get_code_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while fetching a verification code from the repository.
    """
    mocks: DependeciesMocked = mocks_factory(active_user, None)

    mocks.uow.code_repo.get_by_user_id_and_code.side_effect = (
        InfrastructureError(
            'Error attempting to get verification code',
            InfrastructureErrorCode.DATABASE,
            Exception(),
        )
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_code_state_corrupted(
    active_user: User,
):
    """
    The returned verification code instance may raise a domain
    error when built in the repository layer.
    """
    mocks: DependeciesMocked = mocks_factory(active_user, None)

    mocks.uow.code_repo.get_by_user_id_and_code.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()

    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_user_not_found(
    create_unused_code,
):
    """
    The email change flow is aborted when the authenticated user
    does not exist.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        None,
        unused_code,
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_user_inactive(
    inactive_user: User,
    create_unused_code,
):
    """
    The email change flow is aborted when the authenticated user
    is inactive.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        inactive_user,
        unused_code,
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_get_user_fails(
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while fetching a user from the repository.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        None,
        unused_code,
    )

    mocks.uow.user_repo.get_by_public_id.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_user_state_corrupted(
    create_unused_code,
):
    """
    The returned user instance may raise a domain error when built
    in the repository layer.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        None,
        unused_code,
    )

    mocks.uow.user_repo.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()

    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_persist_user_update_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while persisting user changes.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.user_repo.update.side_effect = InfrastructureError(
        'Error attempting to update user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    mocks.uow.user_repo.update.assert_awaited_once()

    # assert was not called
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_persist_code_update_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while persisting verification code changes.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.code_repo.update.side_effect = InfrastructureError(
        'Error attempting to update verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.code_repo.update.assert_awaited_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_awaited()
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_persist_message_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while persisting the notification message.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist message',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.code_repo.update.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.revoke_all.assert_not_awaited()


async def test_change_email_fails_when_revoke_refresh_tokens_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while revoking refresh tokens.
    """
    unused_code = create_unused_code(CodeType.CHANGE_EMAIL, payload_new_email)
    mocks: DependeciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.token_repo.revoke_all.side_effect = InfrastructureError(
        'Error attempting to revoke refresh tokens',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangeEmailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '')

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.code_repo.update.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()
    mocks.uow.token_repo.revoke_all.assert_awaited_once()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies for the
    change email use case.
    """

    token_manager: AsyncMock
    uow: AsyncMock


def mocks_factory(
    user: User | None,
    verification_code: VerificationCode | None,
    token_exists: bool = True,
    token_revoked: bool = False,
) -> DependeciesMocked:
    """
    Create mocked dependencies for the change email use case.

    The configured mocks simulate token validation, token persistence,
    verification code lookup, user lookup, and transactional
    persistence operations used during the email change flow.
    """

    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_manager = AsyncMock(spec=TokenManagerPort)
    # Simulate a validated token payload returned by token manager.
    token_manager.validate.return_value = PayloadTokenDTO(
        jti='jti',
        sub=cast(uuid.UUID, user.public_id if user else None),
        exp=int(exp.timestamp()),
        typ='access',
    )

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.user_repo.update.return_value = None
    # Simulate a persisted user returned by repository lookup.
    uow.user_repo.get_by_public_id.return_value = user

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.update.return_value = None
    # Simulate a persisted verification code returned by repository lookup.
    uow.code_repo.get_by_user_id_and_code.return_value = verification_code

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    uow.token_repo = AsyncMock(spec=RefreshTokenRepositoryPort)
    uow.token_repo.revoke_all.return_value = None
    uow.token_repo.exists.return_value = token_exists
    uow.token_repo.is_revoked.return_value = token_revoked

    return DependeciesMocked(
        token_manager,
        uow,
    )
