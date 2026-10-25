from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from auth_service.adapters.outputs.repositories.message_repository import (
    PostgresMessageRepository,
)
from auth_service.application.exceptions import InfrastructureError
from auth_service.application.messages.message import Message, MessageStatus
from auth_service.application.messages.message_enums import MessageType
from auth_service.application.messages.payload import VerificationCodePayload


async def find_pending_messages_success(
    conn_rollback: AsyncConnection,
):
    # arrange
    payload = VerificationCodePayload(
        recipient='email@email.com',
        code='123456',
    )

    repository = PostgresMessageRepository(conn_rollback)

    # Create not published message
    await repository.create(
        Message(
            type=MessageType.ACCOUNT_DELETION_CODE,
            payload=payload,
            status=MessageStatus.PENDING,
        )
    )

    await repository.create(
        Message(
            type=MessageType.CHANGE_PASSWORD_CODE,
            payload=payload,
            status=MessageStatus.PENDING,
        )
    )

    # Create published messages
    await repository.create(
        Message(
            type=MessageType.RESET_PASSWORD_CODE,
            payload=payload,
            published_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            status=MessageStatus.PUBLISHED,
        )
    )

    await repository.create(
        Message(
            type=MessageType.EMAIL_VERIFICATION_CODE,
            payload=payload,
            published_at=datetime.now(timezone.utc) + timedelta(minutes=15),
            status=MessageStatus.PUBLISHED,
        )
    )

    EMAIL_MESSAGE_TYPES = (
        MessageType.EMAIL_VERIFICATION_CODE,
        MessageType.NOTIFY_EMAIL_VERIFIED,
        MessageType.RESET_PASSWORD_CODE,
        MessageType.NOTIFY_PASSWORD_RESET,
        MessageType.CHANGE_PASSWORD_CODE,
        MessageType.NOTIFY_PASSWORD_CHANGED,
        MessageType.CHANGE_EMAIL_CODE,
        MessageType.NOTIFY_EMAIL_CHANGED,
        MessageType.ACCOUNT_DELETION_CODE,
        MessageType.NOTIFY_ACCOUNT_DELETED,
    )

    # act
    messages = await repository.find_pending_messages_by_type(types=EMAIL_MESSAGE_TYPES)

    # asserts
    number_messages = 2
    assert len(messages) == number_messages

    assert messages[0].type == MessageType.ACCOUNT_DELETION_CODE
    assert messages[0].published_at is None
    assert messages[0].status == MessageStatus.PENDING

    assert messages[1].type == MessageType.CHANGE_PASSWORD_CODE
    assert messages[1].published_at is None
    assert messages[1].status == MessageStatus.PENDING


async def test_find_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection,
    message: Message,
    monkeypatch,
):
    # arrange
    repository = PostgresMessageRepository(conn_rollback)

    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Database error')

    monkeypatch.setattr(
        AsyncConnection,
        'execute',
        mock_execute,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await repository.find_pending_messages_by_type(
            types=[MessageType.ACCOUNT_DELETION_CODE]
        )

    monkeypatch.undo()
