from datetime import datetime, timedelta, timezone

import pytest

from application.messages.email_payloads import EmailVerificationPayload
from application.messages.message import Message
from application.messages.message_types import MessageType

payload = EmailVerificationPayload(
    to='email@email.com',
    code='123456',
)


@pytest.fixture
def message():
    return Message(
        type=MessageType.DELETE_CODE,
        payload=payload,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
