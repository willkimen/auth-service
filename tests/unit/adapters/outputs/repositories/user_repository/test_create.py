from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from auth_service.adapters.outputs.repositories.user_repository import (
    PostgresUserRepository,
)
from auth_service.application.exceptions import InfrastructureError
from auth_service.domain.entities.user import User


async def test_creation_fails_when_database_error_occurs(user: User):
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresUserRepository(mock_conn)

    error_message = 'Failed to create user'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.create(user)
