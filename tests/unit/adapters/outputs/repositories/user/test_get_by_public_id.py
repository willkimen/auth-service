import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.models import UserRowMapper
from adapters.outputs.repositories.user import PostgresUserRepository
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
)


async def test_retrieval_by_public_id_fails_when_database_error_occurs():
    # arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresUserRepository(mock_conn)

    # act and assert
    with pytest.raises(InfrastructureError) as exc_info:
        await repository.get_by_public_id(uuid.uuid4())

    assert 'User retrieval operation failed' in str(exc_info.value)


async def test_retrieval_by_id_fails_when_mapper_cannot_reconstruct_user(
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
        await repository.get_by_public_id(uuid.uuid4())
