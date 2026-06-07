import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.message_repository import (
    PostgresMessageRepository,
)
from application.exceptions import InfrastructureError
from application.messages.message import Message


async def test_should_successfully_create_a_message(
    conn_rollback: AsyncConnection,
    message: Message,
):
    # arrange
    repository = PostgresMessageRepository(conn_rollback)

    # act
    await repository.create(message)

    # assert
    query = sqlalchemy.text(
        """
        SELECT
            id,
            payload,
            type,
            created_at,
            expires_at,
            dispatched_at,
            dispatch_attempts,
            max_attempts
        FROM messages
        WHERE id = :id
        """
    )

    row = (
        await conn_rollback.execute(
            query,
            {'id': message.id},
        )
    ).fetchone()

    assert row is not None
    assert row.id == message.id
    assert row.payload == message.payload.to_dict()
    assert row.type == message.type
    assert row.created_at == message.created_at
    assert row.expires_at == message.expires_at
    assert row.dispatched_at == message.dispatched_at
    assert row.dispatch_attempts == message.dispatch_attempts
    assert row.max_attempts == message.max_attempts


async def test_creation_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection,
    monkeypatch,
    message: Message,
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
        await repository.create(message)

    monkeypatch.undo()

    # ensure NOTHING was persisted
    query = sqlalchemy.text(
        """
        SELECT id
        FROM messages
        WHERE id = :id
        """
    )

    row = (
        await conn_rollback.execute(
            query,
            {'id': message.id},
        )
    ).fetchone()

    assert row is None
