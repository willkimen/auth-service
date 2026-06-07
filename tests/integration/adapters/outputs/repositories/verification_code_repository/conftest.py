import uuid
from datetime import datetime, timedelta, timezone

import pytest

from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.value_objects.code import Code


@pytest.fixture
def verification_code():
    return VerificationCode(
        code=Code('123456'),
        user_public_id=uuid.uuid4(),
        type=CodeType.CHANGE_PASSWORD,
        created_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
        used_at=None,
        payload=None,
    )
