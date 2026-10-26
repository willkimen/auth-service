import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from auth_service.adapters.outputs.repositories.message_repository import (
    PostgresMessageRepository,
)
from auth_service.application.exceptions import InfrastructureError
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_enums import (
    MessageFailureCode,
    MessageStatus,
)


async def test_should_successfully_update_a_message(
    conn_rollback: AsyncConnection,
    message: Message,
    select_message_by_id: sqlalchemy.TextClause,
):
    # arrange
    repository = PostgresMessageRepository(conn_rollback)
    await repository.create(message)

    message.status = MessageStatus.FAILED
    message.publish_attempts += 1
    message.failure_code = MessageFailureCode.BROKER_UNAVAILABLE
    message.failure_reason = 'Connection lost'

    # act
    await repository.update(message)

    # assert
    row = (
        await conn_rollback.execute(
            select_message_by_id,
            {'id': message.id},
        )
    ).fetchone()

    assert row is not None
    assert row.id == message.id
    assert row.status == message.status
    assert row.published_at == message.published_at
    assert row.publish_attempts == message.publish_attempts
    assert row.failure_code == message.failure_code
    assert row.failure_reason == message.failure_reason


async def test_update_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection,
    monkeypatch,
    message: Message,
    select_message_by_id: sqlalchemy.TextClause,
):
    # arrange
    repository = PostgresMessageRepository(conn_rollback)
    await repository.create(message)

    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Database error')

    monkeypatch.setattr(
        AsyncConnection,
        'execute',
        mock_execute,
    )

    message.status = MessageStatus.FAILED
    message.publish_attempts += 1
    message.failure_code = MessageFailureCode.BROKER_UNAVAILABLE
    message.failure_reason = 'Connection lost'

    # act and assert
    with pytest.raises(InfrastructureError):
        await repository.update(message)

    monkeypatch.undo()

    # ensure the persisted message was not updated
    row = (
        await conn_rollback.execute(
            select_message_by_id,
            {'id': message.id},
        )
    ).fetchone()

    assert row is not None
    assert row.status != message.status
    assert row.publish_attempts != message.publish_attempts
    assert row.failure_code != message.failure_code
    assert row.failure_reason != message.failure_reason
