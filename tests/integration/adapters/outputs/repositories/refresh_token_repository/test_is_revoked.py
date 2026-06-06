import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.refresh_token_repository import (
    PostgresRefreshTokenRepository,
)


async def test_should_return_true_when_token_is_revoked(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresRefreshTokenRepository(conn_rollback)

    token_id = 'test-jti-123'
    user_id = uuid.uuid4()
    expiration = datetime.now(timezone.utc) + timedelta(days=1)

    await repository.create(
        sub=user_id,
        jti=token_id,
        expires_at=expiration,
    )
    await repository.revoke(token_id)

    # act
    result = await repository.is_revoked(token_id)

    # assert
    assert result is True


async def test_should_return_false_when_token_is_active(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresRefreshTokenRepository(conn_rollback)

    token_id = 'test-jti-789'
    user_id = uuid.uuid4()

    expiration = datetime.now(timezone.utc) + timedelta(days=1)

    await repository.create(
        sub=user_id,
        jti=token_id,
        expires_at=expiration,
    )

    # act
    result = await repository.is_revoked(token_id)

    # assert
    assert result is False
