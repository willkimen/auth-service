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
    TokenManagerPort,
    TokenRepositoryPort,
    UserRepositoryPort,
)
from application.use_cases.token.refresh import RefreshUseCase
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
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    result = await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(refresh_input)
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.user_repo.is_active.assert_called_once_with(verified_user.public_id)
    mocks.token_manager.new_access.assert_called_once_with(
        verified_user.public_id
    )

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
        InfrastructureErrorCode.AUTH_TOKEN,
        Exception(),
    )
    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.exists.assert_not_called()
    mocks.token_repo.is_revoked.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()


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
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.exists.assert_not_called()
    mocks.token_repo.is_revoked.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()


async def test_refresh_aborts_when_token_is_invalid(
    verified_user: User,
):
    """
    The refresh flow is aborted when token validation fails due to a
    domain token error.
    """
    mocks = mocks_factory(verified_user)

    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.INVALID
    )
    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InvalidTokenError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.exists.assert_not_called()
    mocks.token_repo.is_revoked.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.user_repo.is_active.assert_not_called()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_token_exists_check_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when token existence check fails due to
    an infrastructure error.
    """
    mocks = mocks_factory(verified_user)

    mocks.token_repo.exists.side_effect = InfrastructureError(
        'Error checking token existence',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()

    # assert was not called
    mocks.token_repo.is_revoked.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.user_repo.is_active.assert_not_called()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_token_not_found(
    verified_user: User,
):
    """
    The refresh flow is aborted when the token does not exist in
    persistence storage.
    """
    mocks = mocks_factory(verified_user)

    mocks.token_repo.exists.return_value = False

    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(TokenNotFoundError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()

    # assert was not called
    mocks.token_repo.is_revoked.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.user_repo.is_active.assert_not_called()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_token_revocation_check_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when token revocation check fails due
    to an infrastructure error.
    """
    mocks = mocks_factory(verified_user)

    mocks.token_repo.is_revoked.side_effect = InfrastructureError(
        'Error checking token revocation',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()

    # assert was not called
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.user_repo.is_active.assert_not_called()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_token_is_revoked(
    verified_user: User,
):
    """
    The refresh flow is aborted when the refresh token is revoked.
    """
    mocks = mocks_factory(verified_user)

    mocks.token_repo.is_revoked.return_value = True

    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(TokenRevokedError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()

    # assert was not called
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.user_repo.is_active.assert_not_called()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_get_user_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when user retrieval fails due to an
    infrastructure error.
    """
    mocks = mocks_factory(verified_user)

    mocks.user_repo.get_by_public_id.side_effect = InfrastructureError(
        'Error fetching user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()

    # assert was not called
    mocks.user_repo.is_active.assert_not_called()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_user_state_is_corrupted(
    verified_user: User,
):
    """
    The refresh flow is aborted when the persisted user state cannot
    be reconstructed into a valid domain entity.
    """
    mocks = mocks_factory(verified_user)

    mocks.user_repo.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('corrupted user state'))
    )

    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()

    # assert was not called
    mocks.user_repo.is_active.assert_not_called()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_user_is_not_found(
    verified_user: User,
):
    """
    The refresh flow is aborted when the authenticated user
    cannot be found.
    """
    mocks = mocks_factory(verified_user)

    mocks.user_repo.get_by_public_id.return_value = None

    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(UserNotFoundError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()

    # assert was not called
    mocks.user_repo.is_active.assert_not_called()
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_user_active_check_fails(
    verified_user: User,
):
    """
    The refresh flow is aborted when user active status check fails
    due to an infrastructure error.
    """
    mocks = mocks_factory(verified_user)
    mocks.user_repo.is_active.side_effect = InfrastructureError(
        'Error checking user active status',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.user_repo.is_active.assert_called_once()

    # assert was not called
    mocks.token_manager.new_access.assert_not_called()


async def test_refresh_aborts_when_user_is_inactive(
    verified_user: User,
):
    """
    The refresh flow is aborted when the authenticated user
    is inactive.
    """
    mocks = mocks_factory(verified_user)

    mocks.user_repo.is_active.return_value = False

    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InactiveUserError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.user_repo.is_active.assert_called_once()

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
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = RefreshUseCase(
        user_repo=mocks.user_repo,
        token_manager=mocks.token_manager,
        token_repo=mocks.token_repo,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(refresh_input)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoked.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.user_repo.is_active.assert_called_once()
    mocks.token_manager.new_access.assert_called_once()


@dataclass(frozen=True)
class DependenciesMocked:
    user_repo: AsyncMock
    token_repo: AsyncMock
    token_manager: Mock


def mocks_factory(user: User | None) -> DependenciesMocked:
    user_repo = AsyncMock(spec=UserRepositoryPort)
    user_repo.get_by_public_id.return_value = user
    user_repo.is_active.return_value = True

    token_repo = AsyncMock(spec=TokenRepositoryPort)
    token_repo.exists.return_value = True
    token_repo.is_revoked.return_value = False

    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_manager = Mock(spec=TokenManagerPort)
    token_manager.validate.return_value = PayloadTokenDTO(
        jti=jti,
        sub=cast(uuid.UUID, user.public_id if user else None),
        exp=int(exp.timestamp()),
        typ='refresh',
    )

    token_manager.new_access.return_value = 'access-token'

    return DependenciesMocked(
        user_repo=user_repo,
        token_repo=token_repo,
        token_manager=token_manager,
    )
