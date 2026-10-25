from datetime import datetime, timedelta, timezone

import pytest

from auth_service.application.messages.message import Message
from auth_service.application.messages.message_enums import MessageType
from auth_service.application.messages.payload import VerificationCodePayload

payload = VerificationCodePayload(
    recipient='email@email.com',
    code='123456',
)


@pytest.fixture
def message():
    return Message(
        type=MessageType.ACCOUNT_DELETION_CODE,
        payload=payload,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
