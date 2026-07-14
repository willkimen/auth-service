from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy

from application.messages.email_payloads import EmailCodePayload
from application.messages.message import Message
from application.messages.message_types import MessageType

payload = EmailCodePayload(
    to='email@email.com',
    code='123456',
)


@pytest.fixture
def message():
    return Message(
        type=MessageType.ACCOUNT_DELETION_CODE,
        payload=payload,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )


@pytest.fixture
def select_message_by_id() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
            SELECT *
            FROM messages
            WHERE id = :id
        """
    )


@pytest.fixture
def select_id_column_by_id() -> sqlalchemy.TextClause:
    return sqlalchemy.text(
        """
            SELECT id
            FROM messages
            WHERE id = :id
        """
    )
