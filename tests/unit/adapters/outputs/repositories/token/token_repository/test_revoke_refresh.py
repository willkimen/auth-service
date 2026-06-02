from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.token.token_repository import (
    RefreshTokenRepository,
)
from application.exceptions import InfrastructureError


async def test_revocation_fails_when_database_error_occurs():
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')
    repository = RefreshTokenRepository(mock_conn)

    token_id = 'test-jti-123'

    # act and assert
    with pytest.raises(InfrastructureError) as exc_info:
        await repository.revoke_refresh(token_id)

    assert 'Update operation failed' in str(exc_info.value)
