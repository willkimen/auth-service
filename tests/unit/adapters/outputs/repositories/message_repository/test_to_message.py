from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.engine import RowMapping

from auth_service.adapters.outputs.repositories.message_repository import (
    PostgresMessageRepository,
)
from auth_service.application.exceptions import InfrastructureError
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_types import MessageType
from auth_service.application.messages.payload import (
    NotificationPayload,
    VerificationCodePayload,
)


@pytest.fixture
def message_row() -> RowMapping:
    return {
        'id': uuid4(),
        'payload': {
            'recipient': 'user@example.com',
            'code': '123456',
        },
        'type': MessageType.EMAIL_VERIFICATION_CODE.value,
        'created_at': datetime.now(timezone.utc),
        'expires_at': None,
        'published_at': None,
        'publish_attempts': 0,
    }


def test_to_message_converts_row_to_message(message_row):
    message = PostgresMessageRepository._to_message(message_row)

    assert isinstance(message, Message)
    assert message.id == message_row['id']
    assert message.type == MessageType.EMAIL_VERIFICATION_CODE
    assert message.created_at == message_row['created_at']
    assert message.expires_at is None
    assert message.published_at is None
    assert message.publish_attempts == 0


def test_to_message_reconstructs_verification_code_payload(message_row):
    message = PostgresMessageRepository._to_message(message_row)

    assert isinstance(message.payload, VerificationCodePayload)
    assert message.payload.recipient == 'user@example.com'
    assert message.payload.code == '123456'


def test_to_message_reconstructs_notification_payload(message_row):
    message_row['type'] = MessageType.NOTIFY_EMAIL_VERIFIED.value
    message_row['payload'] = {
        'recipient': 'user@example.com',
    }

    message = PostgresMessageRepository._to_message(message_row)

    assert isinstance(message.payload, NotificationPayload)
    assert message.payload.recipient == 'user@example.com'


def test_to_message_raises_infrastructure_error_for_unknown_message_type(
    message_row,
):
    message_row['type'] = 'UNKNOWN_MESSAGE_TYPE'

    with pytest.raises(
        InfrastructureError,
        match='Failed to reconstruct message from database row',
    ):
        PostgresMessageRepository._to_message(message_row)
