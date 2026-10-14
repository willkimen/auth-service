from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from auth_service.adapters.outputs.repositories.message_repository import (
    PostgresMessageRepository,
)
from auth_service.application.exceptions import InfrastructureError
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_types import MessageType


async def test_find_fails_when_database_error_occurs(
    message: Message,
):
    # arrange
    mock_conn = AsyncMock()

    mock_conn.execute.side_effect = SQLAlchemyError('Database connection lost')

    repository = PostgresMessageRepository(mock_conn)

    error_mesage = 'Failed to retrieve pending messages'

    # act and assert
    with pytest.raises(InfrastructureError, match=error_mesage):
        await repository.find_pending_messages_by_type(
            types=[MessageType.ACCOUNT_DELETION_CODE]
        )
