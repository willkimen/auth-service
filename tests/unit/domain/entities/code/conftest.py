from datetime import datetime, timedelta, timezone

import pytest

from domain.enums import CodeType


@pytest.fixture
def initial_state() -> dict:
    """Provides an initial state for VerificationCode tests.

    Simulates a newly created code with valid default data.
    """
    created_at = datetime.now(timezone.utc) - timedelta(days=1)
    expires_at = created_at + timedelta(days=7)

    return {
        'code': None,
        'user_id': 100,
        'type': CodeType.ACCOUNT_ACTIVATION,
        'created_at': created_at,
        'expires_at': expires_at,
    }
