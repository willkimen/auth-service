import uuid
from datetime import datetime, timezone

import pytest


@pytest.fixture
def user_data_initial() -> dict:
    now = datetime.now(timezone.utc)
    return {
        'public_id': uuid.uuid4(),
        'email': 'user@email.com',
        'plain_password': 'Password!10',
        'email_verified': False,
        'is_active': False,
        'created_at': now,
        'updated_at': now,
        'last_login_at': None,
    }
