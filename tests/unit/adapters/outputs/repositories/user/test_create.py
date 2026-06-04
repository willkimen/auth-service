from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.user import PostgresUserRepository
from application.exceptions import InfrastructureError
from domain.entities.user import User


async def test_creation_fails_when_database_error_occurs(user: User):
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresUserRepository(mock_conn)

    error_message = 'Failed to create user'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.create(user)
