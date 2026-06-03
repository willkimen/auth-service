from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.token.refresh_token import (
    PostgresRefreshTokenRepository,
)
from application.exceptions import InfrastructureError


async def test_revocation_fails_when_database_error_occurs():
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')
    repository = PostgresRefreshTokenRepository(mock_conn)

    error_message = 'Operation to revoke user refresh failed'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.revoke('test-jti-123')
