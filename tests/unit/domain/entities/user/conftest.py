import uuid
from datetime import datetime, timezone

import pytest

from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


@pytest.fixture
def initial_state() -> dict:
    """Provides an initial state for User tests.

    Simulates a newly created user with valid default data.
    """
    now = datetime.now(timezone.utc)

    return {
        'public_id': uuid.uuid4(),
        'email': Email('user@email.com'),
        'hash_password': PasswordHash(b'somepassword'),
        'email_verified': False,
        'is_active': False,
        'created_at': now,
        'updated_at': now,
        'last_login_at': None,
    }
