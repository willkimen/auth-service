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
    TokenManagerPort,
    TokenRepositoryPort,
    UnitOfWorkPort,
)
from application.use_cases.token.revoke_all_refreshes import (
    RevokeAllRefreshesUseCase,
)

jti = 'jti'
token = 'refresh'


async def test_revoke_all_refreshes_successfully():
    """
    Test if the revoke all refreshes use case executes successfully.
    """
    mocks = mocks_factory()
    use_case = RevokeAllRefreshesUseCase(
        uow=mocks.uow,
        token_manager=mocks.token_manager,
    )

    # act
    await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.revoke_all_refreshes.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


async def test_revoke_all_refreshes_aborts_when_invalid_token():
    """
    The revoke all refreshes flow is aborted when token validation
    fails with a domain-level token error.
    """
    mocks = mocks_factory()
    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.INVALID
    )
    use_case = RevokeAllRefreshesUseCase(
        uow=mocks.uow,
        token_manager=mocks.token_manager,
    )

    with pytest.raises(InvalidTokenError):
        await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_revoke_all_refreshes_aborts_when_token_validation_fails():
    """
    The revoke all refreshes flow is aborted when token validation
    fails due to an infrastructure error.
    """
    mocks = mocks_factory()
    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error validating token',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = RevokeAllRefreshesUseCase(
        uow=mocks.uow,
        token_manager=mocks.token_manager,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_revoke_all_refreshes_aborts_when_token_type_is_invalid():
    mocks = mocks_factory()
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    mocks.token_manager.validate.return_value = PayloadTokenDTO(
        jti='jti',
        sub=uuid.uuid4(),
        exp=int(exp.timestamp()),
        typ='access',  # incorrect type
    )
    use_case = RevokeAllRefreshesUseCase(
        uow=mocks.uow,
        token_manager=mocks.token_manager,
    )

    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_revoke_all_refreshes_aborts_when_refresh_revocation_fails():
    """
    The revoke all refreshes flow is aborted when refresh token
    revocation fails due to an infrastructure error.
    """
    mocks = mocks_factory()
    mocks.uow.token_repo.revoke_all_refreshes.side_effect = (
        InfrastructureError(
            'Error revoking refresh tokens',
            InfrastructureErrorCode.DATABASE,
            Exception(),
        )
    )
    use_case = RevokeAllRefreshesUseCase(
        uow=mocks.uow,
        token_manager=mocks.token_manager,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.revoke_all_refreshes.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


@dataclass(frozen=True)
class DependenciesMocked:
    uow: AsyncMock
    token_manager: Mock


def mocks_factory() -> DependenciesMocked:
    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.token_repo = AsyncMock(spec=TokenRepositoryPort)
    uow.token_repo.revoke_all_refreshes.return_value = None

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
