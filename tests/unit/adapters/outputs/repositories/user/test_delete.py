import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.user import PostgresUserRepository
from application.exceptions import InfrastructureError


async def test_delete_fails_when_database_error_occurs():
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresUserRepository(mock_conn)

    error_message = 'User delete operation failed'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.delete(uuid.uuid4())
