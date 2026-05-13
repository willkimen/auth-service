from typing import Callable
from unittest.mock import AsyncMock, Mock

import pytest

from application.dto.user_dto import UserPersistenceDTO
from application.ports.output import (
    HasherPort,
    MessagePublisherPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from unit.application.use_cases.user.types import (
    RegisterUserDependencies,
    SendEmailVerificationCodeDependencies,
)


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


@pytest.fixture
def send_email_verification_code_dependencies() -> Callable[
    [UserPersistenceDTO], SendEmailVerificationCodeDependencies
]:
    def dependecies(user_persitence_dto: UserPersistenceDTO):
        user_repo = AsyncMock(spec=UserRepositoryPort)
        user_repo.get_by_email.return_value = user_persitence_dto

        uow = AsyncMock(spec=UnitOfWorkPort)
        uow.__aenter__.return_value = uow
        uow.__aexit__.return_value = False

        uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
        uow.code_repo.create.return_value = None

        uow.publisher = AsyncMock(spec=MessagePublisherPort)
        uow.publisher.publish.return_value = None

        return SendEmailVerificationCodeDependencies(user_repo, uow)

    return dependecies
