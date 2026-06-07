from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.verification_code_repository import (
    PostgresVerificationCodeRepository,
)
from application.exceptions import InfrastructureError
from domain.entities.verification_code import VerificationCode


async def test_creation_fails_when_database_error_occurs(
    verification_code: VerificationCode,
):
    # arrange
    mock_conn = AsyncMock()

    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresVerificationCodeRepository(mock_conn)

    error_message = 'Failed to create verification code'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.create(verification_code)
