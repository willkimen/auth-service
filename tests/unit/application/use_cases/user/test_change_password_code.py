import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

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
from application.messages.email_payloads import ChangePasswordPayload
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
from application.use_cases.user.change_password_code import (
    ChangePasswordCodeUseCase,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.exceptions import DomainError, InactiveUserError
from domain.value_objects.code import Code

code_expiration_time = 15
token = 'token'
jti = 'jti'


async def test_initialize_change_password_process_successfully(
    active_user: User,
):
    """
    Test if the complete flow initializing password change
    authorization runs successfully.

    Success is verified by checking if all required operations
    are executed with the correct expected arguments.

    Args:
        active_user (User):
            An active user instance used during the authorization
            flow.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act
    await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )

    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    mocks.uow.code_repo.create.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()

    # assert that code_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a VerificationCode instance,
    # which must contain the following state:
    code_arg: VerificationCode = mocks.uow.code_repo.create.call_args[0][0]

    assert code_arg.user_public_id == active_user.public_id
    assert code_arg.used_at is None
    assert code_arg.payload is None
    assert code_arg.expires_at > code_arg.created_at

    code: Code = code_arg.code
    assert isinstance(code.value, str)
    number_digits = 6
    assert len(code.value) == number_digits
    assert code.value.isdigit()

    # assert that message_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a Message instance, which must
    # contain the following state:
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.type == MessageType.PASSWORD_CHANGE_CODE

    payload: ChangePasswordPayload = message_arg.payload
    assert payload.to == active_user.email.value
    assert payload.code == code_arg.code.value
    assert payload.expiration == str(code_expiration_time)
    assert payload.subject == ('Security code for password change')


async def test_change_password_process_not_initialize_when_token_invalid(
    active_user: User,
):
    """
    Test if the password change authorization process is aborted
    when the provided token is invalid.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.TOKEN_INVALID
    )

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenError):
        await use_case.execute(token, code_expiration_time)

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


async def test_change_process_not_initialize_when_token_validation_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected infrastructure
    error occurs while validating the token.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)

    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error attempting to validate token',
        InfrastructureErrorCode.UNKNOWN_ERROR,
        Exception(),
    )

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, code_expiration_time)

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


async def test_change_process_not_initialize_when_token_type_is_invalid(
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

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute(token, code_expiration_time)

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


async def test_password_change_process_not_initialize_when_token_check_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while checking if the token exists in persistence.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.token_repo.exists.side_effect = InfrastructureError(
        'Error attempting to check token existence',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )
    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)

    # assert was not called
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_initialize_when_token_not_found(
    active_user: User,
):
    """
    The password change code generation flow is aborted if the token
    does not exist in persistence storage.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.token_repo.exists.return_value = False

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenNotFoundError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)

    # assert was not called
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_initialize_when_token_revoke_check_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while checking if the token is revoked.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.token_repo.is_revoked.side_effect = InfrastructureError(
        'Error attempting to check revoked token',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_initialize_when_token_is_revoked(
    active_user: User,
):
    """
    The password change flow is aborted if the token was revoked.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.token_repo.is_revoked.return_value = True

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenRevokedError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_initialize_when_get_user_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while retrieving the user from persistence.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.user_repo.get_by_public_id.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_initialize_when_user_state_is_corrupted(
    active_user: User,
):
    """
    Test if a corrupted persistence state error is propagated when
    the repository returns invalid persisted user data.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.user_repo.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_initialize_when_user_not_found():
    """
    The password change flow is aborted if the authenticated user
    no longer exists in persistence.
    """
    mocks: DependeciesMocked = mocks_factory(None)

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_inactive_users_cannot_initialize_password_change(
    inactive_user: User,
):
    """
    The password change flow is aborted if the authenticated user
    is inactive.
    """
    mocks: DependeciesMocked = mocks_factory(inactive_user)

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        inactive_user.public_id
    )

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.code_repo.create.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_initialize_when_persist_code_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while persisting the verification code.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.code_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.code_repo.create.assert_awaited_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_initialize_when_persist_message_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while persisting the notification message.
    """
    mocks: DependeciesMocked = mocks_factory(active_user)
    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist message',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = ChangePasswordCodeUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(token, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.code_repo.create.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies for the
    change password code use case.
    """

    token_manager: Mock
    uow: AsyncMock


def mocks_factory(user: User | None) -> DependeciesMocked:
    """
    Create mocked dependencies for the change password code use case.

    The configured mocks simulate token validation, token persistence
    checks, user lookup operations, and transactional persistence
    required during the password change authorization flow.
    """

    token_manager = Mock(spec=TokenManagerPort)
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_manager.validate.return_value = PayloadTokenDTO(
        jti=jti,
        sub=cast(uuid.UUID, user.public_id if user else None),
        exp=int(exp.timestamp()),
        typ='access',
    )

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.token_repo = AsyncMock(spec=RefreshTokenRepositoryPort)
    uow.token_repo.exists.return_value = True
    uow.token_repo.is_revoked.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.user_repo.get_by_public_id.return_value = user

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.create.return_value = None

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    return DependeciesMocked(
        token_manager=token_manager,
        uow=uow,
    )
