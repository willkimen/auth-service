import uuid
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.models import VerificationCodeRowMapper
from adapters.outputs.repositories.verification_code_repository import (
    PostgresVerificationCodeRepository,
)
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
)


async def test_retrieval_fails_when_database_error_occurs():
    # arrange
    mock_conn = AsyncMock()

    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresVerificationCodeRepository(mock_conn)

    error_message = 'Verification code retrieval operation failed'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.get_by_user_id_and_code(
            user_public_id=uuid.uuid4(),
            code='123456',
        )


async def test_retrieval_fails_when_cannot_reconstruct_verification_code(
    monkeypatch,
):
    # arrange
    mock_conn = AsyncMock()

    mock_result = Mock()
    mock_result.one_or_none.return_value = Mock()

    mock_conn.execute.return_value = mock_result

    repository = PostgresVerificationCodeRepository(mock_conn)

    def mock_to_domain(*args, **kwargs):
        raise ValueError('Corrupted data')

    monkeypatch.setattr(
        VerificationCodeRowMapper,
        'to_domain',
        mock_to_domain,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await repository.get_by_user_id_and_code(
            user_public_id=uuid.uuid4(),
            code='123456',
        )
