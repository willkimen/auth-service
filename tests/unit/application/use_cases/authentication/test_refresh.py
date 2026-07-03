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
from application.ports.output import (
    RefreshTokenRepositoryPort,
    TokenManagerPort,
    UnitOfWorkPort,
    UserRepositoryPort,
)
from application.use_cases.authentication.refresh import RefreshUseCase
from domain.entities.user import User
from domain.exceptions import DomainError, InactiveUserError

jti = 'jti'
refresh_input = 'refresh'


async def test_refresh_successfully(verified_user: User):
    """
    The refresh flow executes successfully when the token is valid,
    not revoked, and the user is active.
    """
    mocks = mocks_factory(verified_user)

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    result = await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(refresh_input)
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.tokens.is_revoked.assert_awaited_once()
    mocks.uow.users.get_by_public_id.assert_awaited_once()
    mocks.token_manager.new_access.assert_called_once_with(
        verified_user.public_id
    )
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert result
    assert result == mocks.token_manager.new_access.return_value


async def test_refresh_aborts_when_token_validation_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when token validation fails due to an
    infrastructure error.
    """
    mocks = mocks_factory(verified_user)
    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error validating token',
        InfrastructureErrorCode.AUTH_TOKEN_ERROR,
        Exception(),
    )
    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.tokens.exists.assert_not_awaited()
    mocks.uow.tokens.is_revoked.assert_not_awaited()
    mocks.uow.users.get_by_public_id.assert_not_awaited()


async def test_refresh_aborts_when_token_type_is_invalid(
    verified_user: User,
):
    mocks = mocks_factory(verified_user)
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    mocks.token_manager.validate.return_value = PayloadTokenDTO(
        jti='jti',
        sub=uuid.uuid4(),
        exp=int(exp.timestamp()),
        typ='access',  # incorrect type
    )

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.tokens.exists.assert_not_awaited()
    mocks.uow.tokens.is_revoked.assert_not_awaited()
    mocks.uow.users.get_by_public_id.assert_not_awaited()


async def test_refresh_aborts_when_token_is_invalid(
    verified_user: User,
):
    """
    The refresh flow is aborted when token validation fails due to a
    domain token error.
    """
    mocks = mocks_factory(verified_user)

    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.TOKEN_INVALID
    )
    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InvalidTokenError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.tokens.exists.assert_not_awaited()
    mocks.uow.tokens.is_revoked.assert_not_awaited()
    mocks.uow.users.get_by_public_id.assert_not_awaited()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_token_exists_check_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when token existence check fails due to
    an infrastructure error.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.tokens.exists.side_effect = InfrastructureError(
        'Error checking token existence',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.tokens.is_revoked.assert_not_awaited()
    mocks.uow.users.get_by_public_id.assert_not_awaited()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_token_not_found(
    verified_user: User,
):
    """
    The refresh flow is aborted when the token does not exist in
    persistence storage.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.tokens.exists.return_value = False

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(TokenNotFoundError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.tokens.is_revoked.assert_not_awaited()
    mocks.uow.users.get_by_public_id.assert_not_awaited()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_token_revocation_check_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when token revocation check fails due
    to an infrastructure error.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.tokens.is_revoked.side_effect = InfrastructureError(
        'Error checking token revocation',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )
    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.tokens.is_revoked.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.users.get_by_public_id.assert_not_awaited()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_token_is_revoked(
    verified_user: User,
):
    """
    The refresh flow is aborted when the refresh token is revoked.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.tokens.is_revoked.return_value = True

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(TokenRevokedError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.tokens.is_revoked.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.users.get_by_public_id.assert_not_awaited()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_get_user_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when user retrieval fails due to an
    infrastructure error.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.users.get_by_public_id.side_effect = InfrastructureError(
        'Error fetching user',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.tokens.is_revoked.assert_awaited_once()
    mocks.uow.users.get_by_public_id.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_user_state_is_corrupted(
    verified_user: User,
):
    """
    The refresh flow is aborted when the persisted user state cannot
    be reconstructed into a valid domain entity.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.users.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('corrupted user state'))
    )

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.tokens.is_revoked.assert_awaited_once()
    mocks.uow.users.get_by_public_id.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_user_is_not_found(
    verified_user: User,
):
    """
    The refresh flow is aborted when the authenticated user
    cannot be found.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.users.get_by_public_id.return_value = None

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(UserNotFoundError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.tokens.is_revoked.assert_awaited_once()
    mocks.uow.users.get_by_public_id.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_user_is_inactive(
    inactive_user: User,
):
    """
    The refresh flow is aborted when the authenticated user
    is inactive.
    """
    mocks = mocks_factory(inactive_user)

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InactiveUserError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.tokens.is_revoked.assert_awaited_once()
    mocks.uow.users.get_by_public_id.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_access_token_generation_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when access token generation fails
    due to an infrastructure error.
    """
    mocks = mocks_factory(verified_user)

    mocks.token_manager.new_access.side_effect = InfrastructureError(
        'Error generating access token',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    use_case = RefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.exists.assert_awaited_once()
    mocks.uow.tokens.is_revoked.assert_awaited_once()
    mocks.uow.users.get_by_public_id.assert_awaited_once()
    mocks.token_manager.new_access.assert_called_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


@dataclass(frozen=True)
class DependenciesMocked:
    token_manager: Mock
    uow: AsyncMock


def mocks_factory(user: User | None) -> DependenciesMocked:
    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False
    uow.users = AsyncMock(spec=UserRepositoryPort)
    uow.users.get_by_public_id.return_value = user

    uow.tokens = AsyncMock(spec=RefreshTokenRepositoryPort)
    uow.tokens.exists.return_value = True
    uow.tokens.is_revoked.return_value = False

    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_manager = Mock(spec=TokenManagerPort)
    token_manager.validate.return_value = PayloadTokenDTO(
        jti=jti,
        sub=cast(uuid.UUID, user.public_id if user else None),
        exp=int(exp.timestamp()),
        typ='refresh',
    )

    token_manager.new_access.return_value = 'access-token'

    return DependenciesMocked(token_manager, uow)
