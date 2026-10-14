import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from auth_service.adapters.outputs.repositories.message_repository import (
    PostgresMessageRepository,
)
from auth_service.application.exceptions import InfrastructureError
from auth_service.application.messages.message import Message


async def test_increment_published_attempts_messages_success(
    conn_rollback: AsyncConnection,
    message: Message,
    select_message_by_id: sqlalchemy.TextClause,
):
    # arrange
    repository = PostgresMessageRepository(conn_rollback)
    await repository.create(message)

    # act
    await repository.increment_publish_attempts(message_id=message.id)

    # asserts
    row = (
        await conn_rollback.execute(
            select_message_by_id,
            {'id': message.id},
        )
    ).fetchone()

    number_attempts = 1
    assert row is not None
    assert row.publish_attempts == number_attempts


async def test_increment_published_attempts_fails_when_a_database_error_occurs(
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
        await repository.increment_publish_attempts(message_id=message.id)

    monkeypatch.undo()
