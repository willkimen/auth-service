import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest

from application.dtos.token_dto import (
    AccessTokenDTO,
    PairTokensDTO,
    PayloadTokenDTO,
    RefreshTokenDTO,
)
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidCredentialsError,
)
from application.ports.output import (
    HasherPort,
    TokenManagerPort,
    TokenRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
)
from application.use_cases.token.login import LoginUseCase
from domain.entities.user import User
from domain.exceptions import (
    InactiveUserError,
    UnverifiedEmailError,
)

jti = 'jti'
access_token = 'access'
refresh_token = 'refresh'
password = 'Password@123'


async def test_login_successfully(verified_user: User):
    """
    Test if login use case returns access and refresh tokens.
    """
    mocks = mocks_factory(verified_user)
    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    result: PairTokensDTO = await use_case.execute(
        email=verified_user.email.value,
        password=password,
    )

    mocks.uow.user_repo.get_by_email.assert_awaited_once_with(
        verified_user.email.value
    )
    mocks.hasher.verify_password.assert_called_once()
    mocks.token_manager.new_pair_token.assert_called_once()
    mocks.uow.token_repo.save_refresh.assert_awaited_once()
    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    assert result.access.token == access_token
    assert result.refresh.token == refresh_token
    assert result.refresh.payload.jti == jti
    assert result.refresh.payload.sub == verified_user.public_id


async def test_login_not_performed_when_user_fetch_fails(
    verified_user: User,
):
    """
    The login flow is aborted when user repository fails.
    """
    mocks = mocks_factory(verified_user)
    mocks.uow.user_repo.get_by_email.side_effect = InfrastructureError(
        'Error fetching user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email=verified_user.email.value,
            password=password,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()

    # assert was not called
    mocks.hasher.verify_password.assert_not_called()
    mocks.token_manager.new_pair_token.assert_not_called()
    mocks.uow.token_repo.save_refresh.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_login_not_performed_when_user_state_is_corrupted(
    verified_user: User,
):
    """
    The login flow is aborted when user state is corrupted.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.user_repo.get_by_email.side_effect = (
        CorruptedPersistenceStateError(Exception())
    )

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(
            email=verified_user.email.value,
            password=password,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()

    # assert was not called
    mocks.hasher.verify_password.assert_not_called()
    mocks.token_manager.new_pair_token.assert_not_called()
    mocks.uow.token_repo.save_refresh.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_login_not_performed_when_user_does_not_exist():
    """
    The login flow is aborted when user is not found.
    """
    mocks = mocks_factory(None)

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            email='test@example.com',
            password=password,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()

    # assert was not called
    mocks.hasher.verify_password.assert_not_called()
    mocks.token_manager.new_pair_token.assert_not_called()
    mocks.uow.token_repo.save_refresh.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_login_not_performed_when_password_verification_fails_due_infra(
    verified_user: User,
):
    """
    The login flow is aborted when password verification
    fails due to infra error.
    """
    mocks = mocks_factory(verified_user)
    mocks.hasher.verify_password.side_effect = InfrastructureError(
        'Error verifying password',
        InfrastructureErrorCode.PASSWORD_HASHER,
        Exception(),
    )

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email=verified_user.email.value,
            password=password,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()
    mocks.hasher.verify_password.assert_called_once()

    # assert was not called
    mocks.token_manager.new_pair_token.assert_not_called()
    mocks.uow.token_repo.save_refresh.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_login_not_performed_when_password_verification_fails(
    verified_user: User,
):
    """
    The login flow is aborted when password verification fails.
    """
    mocks = mocks_factory(verified_user)

    mocks.hasher.verify_password.return_value = False

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            email=verified_user.email.value,
            password='wrong-password',
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()
    mocks.hasher.verify_password.assert_called_once()

    # assert was not called
    mocks.token_manager.new_pair_token.assert_not_called()
    mocks.uow.token_repo.save_refresh.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_login_not_performed_when_user_is_inactive(
    inactive_user: User,
):
    """
    The login flow is aborted when user is inactive.
    """

    mocks = mocks_factory(inactive_user)

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(InactiveUserError):
        await use_case.execute(
            email=inactive_user.email.value,
            password=password,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()
    mocks.hasher.verify_password.assert_called_once()

    # assert was not called
    mocks.token_manager.new_pair_token.assert_not_called()
    mocks.uow.token_repo.save_refresh.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_login_not_performed_when_email_is_not_verified(
    unverified_user: User,
):
    """
    The login flow is aborted when email is not verified.
    """
    mocks = mocks_factory(unverified_user)

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(UnverifiedEmailError):
        await use_case.execute(
            email=unverified_user.email.value, password=password
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()
    mocks.hasher.verify_password.assert_called_once()

    # assert was not called
    mocks.token_manager.new_pair_token.assert_not_called()
    mocks.uow.token_repo.save_refresh.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_login_not_performed_when_user_update_fails(
    verified_user: User,
):
    """
    The login flow is aborted when user update fails.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.user_repo.update.side_effect = InfrastructureError(
        'Error updating user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email=verified_user.email.value,
            password=password,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()
    mocks.hasher.verify_password.assert_called_once()
    mocks.token_manager.new_pair_token.assert_called_once()
    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.save_refresh.assert_not_awaited()


async def test_login_not_performed_when_get_pair_fails(
    verified_user: User,
):
    """
    The login flow is aborted when token generation fails due to an
    infrastructure error in the token manager.
    """
    mocks = mocks_factory(verified_user)
    mocks.token_manager.new_pair_token.side_effect = InfrastructureError(
        'Error generating tokens',
        InfrastructureErrorCode.AUTH_TOKEN,
        Exception(),
    )

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email=verified_user.email.value,
            password=password,
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()
    mocks.hasher.verify_password.assert_called_once()
    mocks.token_manager.new_pair_token.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.token_repo.save_refresh.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()


async def test_login_not_performed_when_save_refresh_fails(
    verified_user: User,
):
    """
    The login flow is aborted when refresh token persistence fails.
    """
    mocks = mocks_factory(verified_user)

    mocks.uow.token_repo.save_refresh.side_effect = InfrastructureError(
        'Error saving refresh token',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = LoginUseCase(
        token_manager=mocks.token_manager,
        hasher=mocks.hasher,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email=verified_user.email.value, password=password
        )

    # assert was called
    mocks.uow.user_repo.get_by_email.assert_awaited_once()
    mocks.hasher.verify_password.assert_called_once()
    mocks.token_manager.new_pair_token.assert_called_once()
    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.token_repo.save_refresh.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()


@dataclass(frozen=True)
class DependenciesMocked:
    token_manager: Mock
    hasher: Mock
    uow: AsyncMock


def mocks_factory(user: User | None) -> DependenciesMocked:
    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.user_repo.get_by_email.return_value = user

    uow.token_repo = AsyncMock(spec=TokenRepositoryPort)
    uow.token_repo.save_refresh.return_value = None

    token_manager = Mock(spec=TokenManagerPort)
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    access = AccessTokenDTO(
        token='access',
        payload=PayloadTokenDTO(
            jti='jti',
            sub=cast(uuid.UUID, user.public_id if user else None),
            exp=int(exp.timestamp()),
            typ='access',
        ),
    )
    exp = datetime.now(timezone.utc) + timedelta(days=7)
    refresh = RefreshTokenDTO(
        token='refresh',
        payload=PayloadTokenDTO(
            jti='jti',
            sub=cast(uuid.UUID, user.public_id if user else None),
            exp=int(exp.timestamp()),
            typ='refresh',
        ),
    )
    token_manager.new_pair_token.return_value = PairTokensDTO(
        access=access,
        refresh=refresh,
    )

    hasher = Mock(spec=HasherPort)
    hasher.verify_password.return_value = True

    return DependenciesMocked(
        token_manager=token_manager,
        hasher=hasher,
        uow=uow,
    )
