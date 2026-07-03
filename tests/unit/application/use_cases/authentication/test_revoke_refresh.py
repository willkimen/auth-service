import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidTokenError,
    InvalidTokenErrorCode,
    InvalidTokenTypeError,
)
from application.ports.output import (
    RefreshTokenRepositoryPort,
    TokenManagerPort,
    UnitOfWorkPort,
)
from application.use_cases.authentication.revoke_refresh import (
    RevokeRefreshUseCase,
)

jti = 'jit'
refresh_token = 'refresh'


async def test_revoke_refresh_successfully():
    """
    Test if the revoke refresh use case executes successfully.
    """
    mocks = mocks_factory()
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    # act
    await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(refresh_token)
    mocks.uow.tokens.revoke.assert_awaited_once_with(jti)


async def test_revoke_refresh_aborts_when_invalid_token():
    """
    The revoke refresh flow is aborted when token validation fails
    with a domain-level token error.
    """
    mocks = mocks_factory()
    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.TOKEN_INVALID
    )
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InvalidTokenError):
        await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.tokens.revoke.assert_not_awaited()


async def test_revoke_refresh_aborts_when_token_validation_fails():
    """
    The revoke refresh flow is aborted when token validation fails
    due to an infrastructure error.
    """
    mocks = mocks_factory()
    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error validating token',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.tokens.revoke.assert_not_awaited()


async def test_revoke_refresh_aborts_when_token_type_is_invalid():
    mocks = mocks_factory()
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    mocks.token_manager.validate.return_value = PayloadTokenDTO(
        jti='jti',
        sub=uuid.uuid4(),
        exp=int(exp.timestamp()),
        typ='access',  # incorrect type
    )
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.tokens.revoke.assert_not_awaited()


async def test_revoke_refresh_aborts_when_refresh_revocation_fails():
    """
    The revoke refresh flow is aborted when refresh token revocation
    fails due to an infrastructure error.
    """
    mocks = mocks_factory()
    mocks.uow.tokens.revoke.side_effect = InfrastructureError(
        'Error revoking refresh token',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.tokens.revoke.assert_awaited_once()


@dataclass(frozen=True)
class DependenciesMocked:
    uow: AsyncMock
    token_manager: Mock


def mocks_factory() -> DependenciesMocked:
    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False
    uow.tokens = AsyncMock(spec=RefreshTokenRepositoryPort)
    uow.tokens.revoke.return_value = None

    exp = datetime.now(timezone.utc) + timedelta(days=7)
    token_manager = Mock(spec=TokenManagerPort)
    token_manager.validate.return_value = PayloadTokenDTO(
        jti=jti,
        sub=uuid.uuid4(),
        exp=int(exp.timestamp()),
        typ='refresh',
    )

    return DependenciesMocked(
        uow=uow,
        token_manager=token_manager,
    )
