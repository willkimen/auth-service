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

    # act and assert
    with pytest.raises(InfrastructureError) as exc_info:
        await repository.revoke_all_refreshes(
            sub=uuid.uuid4(),
        )

    assert 'Update operation failed' in str(exc_info.value)
