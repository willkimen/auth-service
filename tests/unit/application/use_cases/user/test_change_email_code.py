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
)
from application.messages.email_payloads import EmailCodePayload
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
from application.use_cases.user.change_email_code import (
    ChangeEmailCodeUseCase,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    DomainError,
    InactiveUserError,
    InvalidEmailError,
)
from domain.value_objects.code import Code

code_expiration_time = 15
token = 'access-token'
new_email = 'new-email@email.com'


async def test_initialize_change_email_process_successfully(
    active_user: User,
):
    """
    Test if the complete flow initializing email change runs
    successfully.

    Success is verified by checking if key methods are called with
    the correct arguments.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act
    await use_case.execute(
        token,
        new_email,
        code_expiration_time,
    )

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.code_repo.create.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()

    # assert that code_repo.create()
    # was called with the correct expected arguments.
    code_arg: VerificationCode = mocks.uow.code_repo.create.call_args[0][0]
    assert code_arg.user_public_id == active_user.public_id
    assert code_arg.used_at is None
    assert code_arg.get_new_email() == new_email
    assert code_arg.expires_at > code_arg.created_at
    assert code_arg.type is CodeType.CHANGE_EMAIL

    code: Code = code_arg.code
    assert isinstance(code.value, str)
    number_digits = 6
    assert len(code.value) == number_digits
    assert code.value.isdigit()

    # assert that message_repo.create()
    # was called with the correct expected arguments.
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.type == MessageType.CHANGE_EMAIL_CODE
    assert message_arg.expires_at == code_arg.expires_at

    payload: EmailCodePayload = message_arg.payload
    assert payload.to == new_email
    assert payload.code == code_arg.code.value


async def test_change_email_process_not_initialize_when_email_invalid(
    active_user: User,
):
    """
    The change email process is aborted when the provided email
    is invalid.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidEmailError):
        await use_case.execute(token, '', code_expiration_time)

    # assert was not called
    mocks.token_manager.validate.assert_not_called()
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_validate_token_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while validating the token.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)

    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error attempting to validate token',
        InfrastructureErrorCode.AUTH_TOKEN_ERROR,
        Exception(),
    )

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_token_invalid(
    active_user: User,
):
    """
    The change email process is aborted when token validation fails.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.TOKEN_INVALID
    )

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_token_type_is_invalid(
    active_user: User,
):
    mocks: DependeciesMocked = mocks_factory(active_user)
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    mocks.token_manager.validate.return_value = PayloadTokenDTO(
        jti='jti',
        sub=uuid.uuid4(),
        exp=int(exp.timestamp()),
        typ='refresh',  # incorrect type
    )

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_token_not_found(
    active_user: User,
):
    """
    The change email process is aborted when the token does not exist
    in persistence.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.token_repo.exists.return_value = False

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenNotFoundError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_token_exists_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while checking token existence.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)

    mocks.uow.token_repo.exists.side_effect = InfrastructureError(
        'Error attempting to verify token existence',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_token_revoked(
    active_user: User,
):
    """
    The change email process is aborted when the token has already
    been revoked.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.token_repo.is_revoked.return_value = True

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenRevokedError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_revoke_check_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while checking if the token is revoked.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)

    mocks.uow.token_repo.is_revoked.side_effect = InfrastructureError(
        'Error attempting to verify revoked token',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_user_not_found():
    """
    The change email process is aborted when the user does not exist.
    """
    mocks: DependeciesMocked = mocks_factory(None)

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_inactive_users_cannot_initialize_change_email_process(
    inactive_user: User,
):
    """
    The change email process is aborted when the user is inactive.
    """
    mocks: DependeciesMocked = mocks_factory(inactive_user)

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_get_user_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to fetch a user from the repository.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)

    mocks.uow.user_repo.get_by_public_id.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_user_state_corrupted(
    active_user: User,
):
    """
    The returned user instance may raise a domain error when built in
    the repository layer. Test if this error propagates to the use
    case, aborting the change email flow.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)

    mocks.uow.user_repo.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_persist_code_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist a verification code in the repository.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)

    mocks.uow.code_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.code_repo.create.assert_awaited_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_email_process_not_initialize_when_message_persist_fails(
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

    use_case = ChangeEmailCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, new_email, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.code_repo.create.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies for the change
    email verification process.
    """

    token_manager: AsyncMock
    uow: AsyncMock


def mocks_factory(user: User | None) -> DependeciesMocked:
    """
    Create mocked dependencies for the change email verification use case.

    The configured mocks simulate token validation, token persistence
    checks, user retrieval, and transactional persistence operations
    used during the email change verification flow.
    """

    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_manager = AsyncMock(spec=TokenManagerPort)
    token_manager.validate.return_value = PayloadTokenDTO(
        # The value is only relevant when a user instance exists.
        sub=cast(uuid.UUID, user.public_id if user else None),
        jti='jti',
        exp=int(exp.timestamp()),
        typ='access',
    )

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.user_repo.get_by_public_id.return_value = user

    uow.token_repo = AsyncMock(spec=RefreshTokenRepositoryPort)
    uow.token_repo.exists.return_value = True
    uow.token_repo.is_revoked.return_value = False

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.create.return_value = None

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    return DependeciesMocked(
        token_manager,
        uow,
    )
