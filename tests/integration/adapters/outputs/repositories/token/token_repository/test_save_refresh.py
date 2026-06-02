import uuid
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.token.token_repository import (
    RefreshTokenRepository,
)
from application.exceptions import InfrastructureError


async def test_should_successfully_persist_a_refresh_token(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = RefreshTokenRepository(conn_rollback)

    token_id = 'test-jti-123'
    user_id = uuid.uuid4()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=15)

    # Act
    await repository.save_refresh(
        sub=user_id,
        jti=token_id,
        expires_at=expiration,
    )

    # assert
    query = sqlalchemy.text(
        """
        SELECT jti, sub, exp, revoked_at, created_at
        FROM refresh_token
        WHERE jti = :jti;
        """
    )
    row = (await conn_rollback.execute(query, {'jti': token_id})).fetchone()

    assert row is not None
    assert row.jti == token_id
    assert row.sub == user_id
    assert row.exp == expiration
    assert row.revoked_at is None
    assert row.created_at < row.exp


async def test_persistence_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection, monkeypatch
):
    # arrange
    repo = RefreshTokenRepository(conn_rollback)
    token_id = 'test-jti-456'
    user_id = uuid.uuid4()
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)

    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Erro de banco')

    monkeypatch.setattr(AsyncConnection, 'execute', mock_execute)

    # act and assert
    # ensure the infrastructure exception is raised
    with pytest.raises(InfrastructureError):
        await repo.save_refresh(sub=user_id, jti=token_id, expires_at=exp)

    # remove the mock to allow querying the real database again
    monkeypatch.undo()

    # ensure NOTHING was persisted in the real database
    query = sqlalchemy.text('SELECT jti FROM refresh_token WHERE jti = :jti')
    res = await conn_rollback.execute(query, {'jti': token_id})
    row = res.fetchone()

    # The record must not exist due to the automatic rollback
    assert row is None
