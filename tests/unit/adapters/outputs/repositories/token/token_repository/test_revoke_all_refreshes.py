import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.token.token_repository import (
    RefreshTokenRepository,
)
from application.exceptions import InfrastructureError


async def test_revocation_fails_when_database_error_occurs():
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.side_effect = SQLAlchemyError()
    repository = RefreshTokenRepository(mock_conn)

    error_message = 'Operation to revoke all user refreshes failed'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_message):
        await repository.revoke_all_refreshes(
            sub=uuid.uuid4(),
        )
