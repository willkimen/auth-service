import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock

import pytest

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
    TokenError,
    TokenErrorCode,
)
from application.ports.output import TokenManagerPort, TokenRepositoryPort
from application.use_cases.token.revoke_refresh import RevokeRefreshUseCase

jti = 'jit'
refresh_token = 'refresh'


async def test_revoke_refresh_successfully():
    """
    Test if the revoke refresh use case executes successfully.
    """
    mocks = mocks_factory()
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    # act
    await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(refresh_token)
    mocks.token_repo.revoke_refresh.assert_called_once_with(jti)


async def test_revoke_refresh_aborts_when_invalid_token():
    """
    The revoke refresh flow is aborted when token validation fails
    with a domain-level token error.
    """
    mocks = mocks_factory()
    mocks.token_manager.validate.side_effect = TokenError(
        TokenErrorCode.INVALID
    )
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(TokenError):
        await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.revoke_refresh.assert_not_called()


async def test_revoke_refresh_aborts_when_token_validation_fails():
    """
    The revoke refresh flow is aborted when token validation fails
    due to an infrastructure error.
    """
    mocks = mocks_factory()
    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error validating token',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.revoke_refresh.assert_not_called()


async def test_revoke_refresh_aborts_when_refresh_revocation_fails():
    """
    The revoke refresh flow is aborted when refresh token revocation
    fails due to an infrastructure error.
    """
    mocks = mocks_factory()
    mocks.token_repo.revoke_refresh.side_effect = InfrastructureError(
        'Error revoking refresh token',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = RevokeRefreshUseCase(
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.revoke_refresh.assert_called_once()


@dataclass(frozen=True)
class DependenciesMocked:
    token_repo: AsyncMock
    token_manager: Mock


def mocks_factory() -> DependenciesMocked:
    token_repo = AsyncMock(spec=TokenRepositoryPort)
    token_repo.revoke_refresh.return_value = None

    token_manager = Mock(spec=TokenManagerPort)

    token_manager.validate.return_value = PayloadTokenDTO(
        jti=jti,
        sub=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )

    return DependenciesMocked(
        token_repo=token_repo,
        token_manager=token_manager,
    )
