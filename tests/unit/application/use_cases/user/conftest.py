import uuid
from datetime import datetime, timezone

import pytest

from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash

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
