import uuid
from datetime import datetime, timezone

import pytest

from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


@pytest.fixture
def user():
    return User(
        public_id=uuid.uuid4(),
        email=Email('email@email.com'),
        hash_password=PasswordHash('hashedpassword'),
        email_verified=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )


@pytest.fixture
def user_data() -> dict:
    return {
        'public_id': uuid.uuid4(),
        'email': 'email@email.com',
        'hash_password': 'hash',
        'email_verified': False,
        'is_active': True,
        'created_at': datetime.now(timezone.utc),
        'updated_at': datetime.now(timezone.utc),
        'last_login_at': None,
    }
