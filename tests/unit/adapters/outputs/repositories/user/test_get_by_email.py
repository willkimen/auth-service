from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.models import UserRowMapper
from adapters.outputs.repositories.user import PostgresUserRepository
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
)


async def test_retrieval_fails_when_database_error_occurs():
    # arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresUserRepository(mock_conn)

    error_message = 'User retrieval operation failed'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.get_by_email('email@email.com')


async def test_retrieval_fails_when_mapper_cannot_reconstruct_user(
    monkeypatch,
):
    # arrange
    mock_conn = AsyncMock()
    mock_result = Mock()
    mock_result.one_or_none.return_value = Mock()
    mock_conn.execute.return_value = mock_result

    repository = PostgresUserRepository(mock_conn)

    def mock_to_domain(*args, **kwargs):
        raise ValueError('Corrupted data')

    monkeypatch.setattr(
        UserRowMapper,
        'to_domain',
        mock_to_domain,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await repository.get_by_email('email@email.com')
