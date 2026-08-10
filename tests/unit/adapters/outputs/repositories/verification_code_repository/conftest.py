import uuid
from datetime import datetime, timedelta, timezone

import pytest

from auth_service.domain.entities.verification_code import VerificationCode
from auth_service.domain.enums import CodeType
from auth_service.domain.value_objects.code import Code


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
