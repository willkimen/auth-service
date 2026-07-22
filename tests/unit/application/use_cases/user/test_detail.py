import uuid
from dataclasses import dataclass, fields
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from application.dtos.token_dto import PayloadTokenDTO
from application.dtos.user_dto import UserPublicDTO
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidTokenError,
    InvalidTokenErrorCode,
    InvalidTokenTypeError,
    UserNotFoundError,
)
from application.ports.output import (
    TokenManagerPort,
    UnitOfWorkPort,
    UserRepositoryPort,
)
from application.use_cases.user.detail import DetailUseCase
from domain.entities.user import User
from domain.exceptions import DomainError, InactiveUserError

access = 'access-token'


async def test_return_user_details_successfully(active_user: User):
    """
    Test if the authenticated user details are returned successfully.
    """
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = PayloadTokenDTO(
        sub=active_user.public_id,
        jti='token-jti',
        exp=int(exp.timestamp()),
        typ='access',
    )

    mocks: DependeciesMocked = mocks_factory(active_user, payload)

    use_case = DetailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act
    actual_user: UserPublicDTO = await use_case.execute(access)

    # assert returned dto
    assert actual_user.public_id == active_user.public_id
    assert actual_user.email == active_user.email.value
    assert actual_user.created_at == active_user.created_at
    assert actual_user.email_verified == active_user.email_verified
    assert actual_user.last_login_at == active_user.last_login_at

    # Assert that the returned fields are the following:
    expected_public_fields = {
        'public_id',
        'email',
        'created_at',
        'email_verified',
        'last_login_at',
    }

    assert {field.name for field in fields(actual_user)} == (
        expected_public_fields
    )

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.uow.users.get_by_public_id.assert_awaited_once_with(payload.sub)
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


async def test_detail_fails_when_token_validation_fails_unexpectedly():
    """
    Test if an exception is raised when token validation fails.
    """
    mocks: DependeciesMocked = mocks_factory(None, None)

    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error validating token',
        InfrastructureErrorCode.AUTH_TOKEN_ERROR,
        Exception(),
    )

    use_case = DetailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(access)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.users.get_by_public_id.assert_not_awaited()


async def test_detail_fails_when_token_type_is_invalid():
    mocks: DependeciesMocked = mocks_factory(None, None)

    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    mocks.token_manager.validate.return_value = PayloadTokenDTO(
        jti='jti',
        sub=uuid.uuid4(),
        exp=int(exp.timestamp()),
        typ='refresh',  # incorrect type
    )

    use_case = DetailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute(access)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.users.get_by_public_id.assert_not_awaited()


async def test_detail_fails_when_token_is_invalid():
    mocks: DependeciesMocked = mocks_factory(None, None)
    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.TOKEN_EXPIRED
    )
    use_case = DetailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenError):
        await use_case.execute('invalid-token')

    # assert was called
    mocks.token_manager.validate.assert_called_once_with('invalid-token')
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.users.get_by_public_id.assert_not_awaited()


async def test_detail_fails_when_user_does_not_exist():
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = PayloadTokenDTO(
        sub=uuid.uuid4(),
        jti='token-jti',
        exp=int(exp.timestamp()),
        typ='access',
    )

    mocks: DependeciesMocked = mocks_factory(None, payload)

    use_case = DetailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute(access)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.uow.users.get_by_public_id.assert_awaited_once_with(payload.sub)
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


async def test_detail_fails_when_get_user_fails():
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to return a user from the repository.
    """
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = PayloadTokenDTO(
        sub=uuid.uuid4(),
        jti='token-jti',
        exp=int(exp.timestamp()),
        typ='access',
    )

    mocks: DependeciesMocked = mocks_factory(None, payload)

    mocks.uow.users.get_by_public_id.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = DetailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(access)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.uow.users.get_by_public_id.assert_awaited_once_with(payload.sub)
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


async def test_detail_fails_when_user_state_is_corrupted():
    """
    The returned user instance may raise a domain error when built in
    the repository layer. Test if this error propagates to the use
    case, aborting the detail flow.
    """
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = PayloadTokenDTO(
        sub=uuid.uuid4(),
        jti='token-jti',
        exp=int(exp.timestamp()),
        typ='access',
    )

    mocks: DependeciesMocked = mocks_factory(None, payload)

    mocks.uow.users.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )

    use_case = DetailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(access)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.uow.users.get_by_public_id.assert_awaited_once_with(payload.sub)
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


async def test_detail_fails_when_user_is_inactive(inactive_user: User):
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    payload = PayloadTokenDTO(
        sub=uuid.uuid4(),
        jti='token-jti',
        exp=int(exp.timestamp()),
        typ='access',
    )

    mocks: DependeciesMocked = mocks_factory(
        inactive_user,
        payload,
    )

    use_case = DetailUseCase(
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute(access)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.uow.users.get_by_public_id.assert_awaited_once_with(payload.sub)
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies for the user
    detail use case.
    """

    uow: AsyncMock
    token_manager: Mock


def mocks_factory(
    user: User | None,
    payload: PayloadTokenDTO | None,
) -> DependeciesMocked:
    """
    Create and configure mocked repositories and token manager
    dependencies for the user detail use case.

    The provided payload simulates the validated token payload
    returned by the token manager.

    The provided user instance simulates a persisted user returned
    by the repository during the execution flow.
    """
    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.users = AsyncMock(spec=UserRepositoryPort)
    uow.users.get_by_public_id.return_value = user

    token_manager = Mock(spec=TokenManagerPort)
    token_manager.validate.return_value = payload

    return DependeciesMocked(
        uow,
        token_manager,
    )
