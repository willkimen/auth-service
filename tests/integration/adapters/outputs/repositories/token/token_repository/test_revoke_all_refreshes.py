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


async def test_should_invalidate_all_active_sessions_for_a_specific_user(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = RefreshTokenRepository(conn_rollback)
    target_user_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=15)

    # we store two active tokens for the target user
    await repository.save_refresh(target_user_id, 'token-1', expiration)
    await repository.save_refresh(target_user_id, 'token-2', expiration)

    # we store one active token for a different user (should remain untouched)
    await repository.save_refresh(other_user_id, 'token-3', expiration)

    # act
    await repository.revoke_all_refreshes(sub=target_user_id)

    # assert
    # we verify that target tokens are revoked and others are not
    query = sqlalchemy.text(
        'SELECT jti, revoked_at FROM refresh_token ORDER BY jti;'
    )
    records = (await conn_rollback.execute(query)).fetchall()

    # tokens 1 and 2 for the target user must have a revocation timestamp
    assert records[0].jti == 'token-1'
    assert records[0].revoked_at is not None

    assert records[1].jti == 'token-2'
    assert records[1].revoked_at is not None

    # token 3 for the other user must remain active (revoked_at is NULL)
    assert records[2].jti == 'token-3'
    assert records[2].revoked_at is None


async def test_revocation_fails_when_database_error_occurs(
    conn_rollback: AsyncConnection, monkeypatch
):
    # arrange
    repo = RefreshTokenRepository(conn_rollback)
    token_id = 'test-jti-999'
    user_id = uuid.uuid4()
    exp = datetime.now(timezone.utc) + timedelta(days=1)

    # insert a real active token into the database
    await repo.save_refresh(
        sub=user_id,
        jti=token_id,
        expires_at=exp,
    )

    # force an error by mocking the AsyncConnection class
    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Erro de banco')

    monkeypatch.setattr(AsyncConnection, 'execute', mock_execute)

    # act and assert
    # ensure the infrastructure exception is raised
    with pytest.raises(InfrastructureError):
        await repo.revoke_all_refreshes(sub=user_id)

    # remove the class mock to restore real database behavior
    monkeypatch.undo()

    # ensure the rollback kept the state intact
    query = sqlalchemy.text(
        'SELECT revoked_at FROM refresh_token WHERE jti = :jti'
    )
    res = await conn_rollback.execute(query, {'jti': token_id})
    row = res.fetchone()

    assert row is not None
    assert row.revoked_at is None
