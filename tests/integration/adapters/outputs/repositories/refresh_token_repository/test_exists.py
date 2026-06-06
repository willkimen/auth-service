import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.refresh_token_repository import (
    PostgresRefreshTokenRepository,
)


async def test_should_return_true_when_token_exists(
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
    result = await repository.exists(token_id)

    # assert
    assert result is True


async def test_should_return_false_when_token_does_not_exist(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresRefreshTokenRepository(conn_rollback)

    token_id = 'non-existent-jti'

    # act
    result = await repository.exists(token_id)

    # assert
    assert result is False
