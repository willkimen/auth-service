import json
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import aio_pika
import pytest

from auth_service.adapters.outputs.messaging.rabbit_email_message_publisher import (
    RabbitMQEmailMessagePublisherAdapter,
)
from auth_service.application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_enums import (
    MessageFailureCode,
    MessageStatus,
    MessageType,
)
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


async def test_publish_succeeds(
    adapter: RabbitMQEmailMessagePublisherAdapter,
    exchange: MagicMock,
    message: Message,
) -> None:
    result = await adapter.publish(message)

    exchange.publish.assert_awaited_once()

    published_message = exchange.publish.await_args.args[0]
    body = json.loads(published_message.body)

    assert body == {
        'id': str(message.id),
        'type': message.type.value,
        'payload': message.payload.to_dict(),
    }
    assert published_message.content_type == 'application/json'
    assert published_message.delivery_mode == aio_pika.DeliveryMode.PERSISTENT

    assert result is message
    assert message.status == MessageStatus.PUBLISHED
    assert message.published_at is not None
    assert message.publish_attempts == 1
    assert message.failure_code is None
    assert message.failure_reason is None


async def test_publish_without_initialization_raises(
    message: Message,
) -> None:
    adapter = RabbitMQEmailMessagePublisherAdapter(MagicMock())

    with pytest.raises(InfrastructureError) as exc_info:
        await adapter.publish(message)

    assert exc_info.value.code == InfrastructureErrorCode.MESSAGING_ERROR
    assert message.publish_attempts == 0


@pytest.mark.parametrize(
    ('exception', 'failure_code', 'expected_status'),
    [
        (
            TypeError('Invalid payload'),
            MessageFailureCode.SERIALIZATION_ERROR,
            MessageStatus.FAILED,
        ),
        (
            ValueError('Invalid JSON value'),
            MessageFailureCode.SERIALIZATION_ERROR,
            MessageStatus.FAILED,
        ),
        (
            aio_pika.exceptions.DeliveryError(
                message=MagicMock(),
                frame=MagicMock(),
            ),
            MessageFailureCode.PUBLISH_REJECTED,
            MessageStatus.PENDING,
        ),
        (
            TimeoutError('Publish timed out'),
            MessageFailureCode.PUBLISH_TIMEOUT,
            MessageStatus.PENDING,
        ),
        (
            aio_pika.exceptions.AMQPException('Broker error'),
            MessageFailureCode.BROKER_UNAVAILABLE,
            MessageStatus.PENDING,
        ),
        (
            OSError('Connection lost'),
            MessageFailureCode.BROKER_UNAVAILABLE,
            MessageStatus.PENDING,
        ),
    ],
)
async def test_publish_records_failure(
    adapter: RabbitMQEmailMessagePublisherAdapter,
    exchange: MagicMock,
    message: Message,
    exception: Exception,
    failure_code: MessageFailureCode,
    expected_status: MessageStatus,
) -> None:
    exchange.publish.side_effect = exception

    result = await adapter.publish(message)

    assert result is message
    assert message.status == expected_status
    assert message.publish_attempts == 1
    assert message.failure_code == failure_code
    assert message.failure_reason == str(exception)


async def test_publish_records_serialization_failure(
    adapter: RabbitMQEmailMessagePublisherAdapter,
    exchange: MagicMock,
    message: Message,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_serialization_error(*args: object, **kwargs: object) -> str:
        raise TypeError('Cannot serialize payload')

    monkeypatch.setattr(
        'auth_service.adapters.outputs.messaging.rabbit_email_message_publisher.json.dumps',
        raise_serialization_error,
    )

    result = await adapter.publish(message)

    exchange.publish.assert_not_awaited()
    assert result is message
    assert message.status == MessageStatus.FAILED
    assert message.publish_attempts == 1
    assert message.failure_code == MessageFailureCode.SERIALIZATION_ERROR
    assert message.failure_reason == 'Cannot serialize payload'
