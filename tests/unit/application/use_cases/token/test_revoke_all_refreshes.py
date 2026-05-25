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
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    # act
    await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.token_repo.revoke_all_refreshes.assert_called_once()


async def test_revoke_all_refreshes_aborts_when_invalid_token():
    """
    The revoke all refreshes flow is aborted when token validation
    fails with a domain-level token error.
    """
    mocks = mocks_factory()
    mocks.token_manager.validate.side_effect = TokenError(
        TokenErrorCode.INVALID
    )
    use_case = RevokeAllRefreshesUseCase(
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(TokenError):
        await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.revoke_all_refreshes.assert_not_called()


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
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.revoke_all_refreshes.assert_not_called()


async def test_revoke_all_refreshes_aborts_when_refresh_revocation_fails():
    """
    The revoke all refreshes flow is aborted when refresh token
    revocation fails due to an infrastructure error.
    """
    mocks = mocks_factory()
    mocks.token_repo.revoke_all_refreshes.side_effect = InfrastructureError(
        'Error revoking refresh tokens',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = RevokeAllRefreshesUseCase(
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(token)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.revoke_all_refreshes.assert_called_once()


@dataclass(frozen=True)
class DependenciesMocked:
    token_repo: AsyncMock
    token_manager: Mock


def mocks_factory() -> DependenciesMocked:
    token_repo = AsyncMock(spec=TokenRepositoryPort)

    token_repo.revoke_all_refreshes.return_value = None

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
