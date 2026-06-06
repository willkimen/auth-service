from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.user_repository import (
    PostgresUserRepository,
)
from application.exceptions import InfrastructureError
from domain.entities.user import User


async def test_update_fails_when_database_error_occurs(user: User):
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresUserRepository(mock_conn)

    error_message = 'User update operation failed'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.update(user)
