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
        email=Email('john@example.com'),
        hash_password=PasswordHash('$2b$12$hashedpassword'),
        email_verified=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )
