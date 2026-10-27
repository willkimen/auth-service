from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from auth_service.adapters.outputs.messaging.rabbit_email_message_publisher import (
    RabbitMQEmailMessagePublisherAdapter,
)
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_enums import MessageStatus, MessageType
from auth_service.application.messages.payload import VerificationCodePayload


@pytest.fixture
def message() -> Message:
    now = datetime.now(UTC)

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
        status=MessageStatus.PENDING,
    )


@pytest.fixture
def exchange() -> MagicMock:
    exchange = MagicMock()
    exchange.publish = AsyncMock()
    return exchange


@pytest.fixture
def adapter(exchange: MagicMock) -> RabbitMQEmailMessagePublisherAdapter:
    adapter = RabbitMQEmailMessagePublisherAdapter(MagicMock())
    adapter._exchange = exchange
    return adapter
