import uuid
from datetime import datetime, timedelta, timezone

import pytest

from domain.enums import CodeType
from domain.value_objects.code import Code


@pytest.fixture
def initial_state() -> dict:
    """Provides an initial state for VerificationCode tests.

    Simulates a newly created code with valid default data.
    """
    created_at = datetime.now(timezone.utc) - timedelta(days=1)
    expires_at = created_at + timedelta(days=7)
    code = Code.generate()

    return {
        'code': code,
        'user_public_id': uuid.uuid4(),
        'type': CodeType.EMAIL_VERIFICATION,
        'created_at': created_at,
        'expires_at': expires_at,
        'sent_at': None,
    }
