from unittest.mock import AsyncMock, Mock

import pytest

from application.ports.output import (
    HasherPort,
    UserRepositoryPort,
)
from unit.application.use_cases.user.types import RegisterUserDependencies


@pytest.fixture
def register_user_dependencies() -> RegisterUserDependencies:
    hasher = Mock(spec=HasherPort)
    hasher.hash.return_value = 'hashed-password'

    user_repo = Mock(spec=UserRepositoryPort)
    user_repo.exists_by_email = AsyncMock(return_value=False)
    user_repo.create = AsyncMock()

    return RegisterUserDependencies(
        hasher=hasher,
        user_repo=user_repo,
    )
