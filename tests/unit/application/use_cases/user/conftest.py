import uuid
from datetime import datetime, timezone
from typing import Callable
from unittest.mock import AsyncMock, Mock

import pytest

from application.dtos.verification_code_dto import (
    VerificationCodePersistenceDTO,
)
from application.ports.output import (
    HasherPort,
    MessageRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash
from unit.application.use_cases.user.types import (
    EmailVerificationDependencies,
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
    [User], SendEmailVerificationCodeDependencies
]:
    def dependecies(
        user: User,
    ) -> SendEmailVerificationCodeDependencies:
        user_repo = AsyncMock(spec=UserRepositoryPort)
        user_repo.get_by_email.return_value = user

        uow = AsyncMock(spec=UnitOfWorkPort)
        uow.__aenter__.return_value = uow
        uow.__aexit__.return_value = False

        uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
        uow.code_repo.create.return_value = None

        uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
        uow.message_repo.create.return_value = None

        return SendEmailVerificationCodeDependencies(user_repo, uow)

    return dependecies


@pytest.fixture
def email_verification_dependencies() -> Callable[
    [User, VerificationCodePersistenceDTO],
    EmailVerificationDependencies,
]:
    def dependecies(
        user: User,
        code_persistence_dto: VerificationCodePersistenceDTO,
    ) -> EmailVerificationDependencies:
        user_repo = AsyncMock(spec=UserRepositoryPort)
        user_repo.get_by_email.return_value = user

        code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
        code_repo.get_by_user_id_and_code.return_value = code_persistence_dto

        uow = AsyncMock(spec=UnitOfWorkPort)
        uow.__aenter__.return_value = uow
        uow.__aexit__.return_value = False

        uow.user_repo = AsyncMock(spec=UserRepositoryPort)
        uow.user_repo.update.return_value = None

        uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
        uow.code_repo.update.return_value = None

        uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
        uow.message_repo.create.return_value = None

        return EmailVerificationDependencies(user_repo, code_repo, uow)

    return dependecies


public_id = uuid.uuid4()
email = Email('email@email.com')
password_hash = PasswordHash('password-hashed')
created_at = datetime.now(timezone.utc)
updated_at = datetime.now(timezone.utc)


@pytest.fixture
def unverified_user() -> User:
    return User(
        public_id=public_id,
        email=email,
        hash_password=password_hash,
        email_verified=False,
        is_active=True,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=None,
    )


@pytest.fixture
def verified_user() -> User:
    return User(
        public_id=public_id,
        email=email,
        hash_password=password_hash,
        email_verified=True,
        is_active=True,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=None,
    )


@pytest.fixture
def inactive_user() -> User:
    return User(
        public_id=public_id,
        email=email,
        hash_password=password_hash,
        email_verified=False,
        is_active=False,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=None,
    )
