import uuid
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.refresh_token_repository import (
    PostgresRefreshTokenRepository,
)
from application.exceptions import InfrastructureError


async def test_should_successfully_revoke_a_refresh_token(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresRefreshTokenRepository(conn_rollback)

    token_id = 'test-jti-123'
    user_id = uuid.uuid4()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=15)

    await repository.create(
        sub=user_id,
        jti=token_id,
        expires_at=expiration,
    )

    # act
    await repository.revoke(token_id)

    # assert
    query = sqlalchemy.text(
        """
        SELECT revoked_at
        FROM refresh_tokens
        WHERE jti = :jti;
        """
    )

    row = (await conn_rollback.execute(query, {'jti': token_id})).fetchone()

    assert row is not None
    assert row.revoked_at is not None
    assert row.revoked_at <= datetime.now(timezone.utc)


async def test_revocation_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection, monkeypatch
):
    # arrange
    repo = PostgresRefreshTokenRepository(conn_rollback)

    token_id = 'test-jti-999'
    user_id = uuid.uuid4()
    exp = datetime.now(timezone.utc) + timedelta(days=1)

    await repo.create(
        sub=user_id,
        jti=token_id,
        expires_at=exp,
    )

    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Erro de banco')

    monkeypatch.setattr(AsyncConnection, 'execute', mock_execute)

    # act and assert
    # ensure the infrastructure exception is raised
    with pytest.raises(InfrastructureError):
        await repo.revoke(token_id)

    # remove the mock to restore real database behavior
    monkeypatch.undo()

    # ensure the rollback kept the state intact
    query = sqlalchemy.text(
        """
        SELECT revoked_at
        FROM refresh_tokens
        WHERE jti = :jti
        """
    )

    res = await conn_rollback.execute(query, {'jti': token_id})
    row = res.fetchone()

    assert row is not None
    assert row.revoked_at is None
