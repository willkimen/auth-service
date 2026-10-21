from datetime import datetime, timedelta, timezone
from uuid import uuid4

import aio_pika
import pytest
import pytest_asyncio

from auth_service.application.messages.message import Message
from auth_service.application.messages.message_types import MessageType
from auth_service.application.messages.payload import VerificationCodePayload


@pytest.fixture
def message() -> Message:
    now = datetime.now(timezone.utc)

    return Message(
        id=uuid4(),
        type=MessageType.EMAIL_VERIFICATION_CODE,
        payload=VerificationCodePayload(
            recipient='test@example.com',
            code='123456',
        ),
        created_at=now,
        expires_at=now + timedelta(minutes=20),
        published_at=None,
    )


@pytest_asyncio.fixture(loop_scope='function')
async def connection():
    connection = await aio_pika.connect_robust('amqp://test:test@localhost:5672/')
    yield connection
    await connection.close()
