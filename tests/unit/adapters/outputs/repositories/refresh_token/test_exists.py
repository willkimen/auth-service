from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.refresh_token import (
    PostgresRefreshTokenRepository,
)
from application.exceptions import InfrastructureError


async def test_query_fails_when_database_error_occurs():
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresRefreshTokenRepository(mock_conn)

    error_message = 'Operation to verify the existence of the token failed'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.exists('test-jti-123')
