import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.token.token_repository import (
    RefreshTokenRepository,
)
from application.exceptions import InfrastructureError


async def test_persistence_fails_when_database_error_occurs():
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')
    repository = RefreshTokenRepository(mock_conn)

    user_id = uuid.uuid4()
    token_id = 'test-jti-123'
    expiration = datetime.now(timezone.utc)

    # act and assert
    with pytest.raises(InfrastructureError) as exc_info:
        await repository.save_refresh(
            sub=user_id,
            jti=token_id,
            expires_at=expiration,
        )

    assert 'Database operation failed' in str(exc_info.value)
