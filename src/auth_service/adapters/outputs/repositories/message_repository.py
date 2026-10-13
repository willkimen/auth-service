from sqlalchemy import JSON, bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from auth_service.application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)
from auth_service.application.messages.message import Message
from auth_service.application.messages.payload import Payload


class PostgresMessageRepository:
    """
    Defines persistence operations for messages.

    A persisted message represents an intention to execute
    a specific operation later.

    Messages store all data required for future processing,
    allowing dedicated components or workers to execute
    the intended operation afterwards.
    """

    def __init__(self, conn: AsyncConnection):
        self.conn = conn

    async def create(self, message: Message) -> None:
        """
        Persists a message containing the data required
        for later processing.

        Raises:
            InfrastructureError:
                Raised when message persistence fails.
        """
        try:
            query = text(
                """
                INSERT INTO messages (
                    id,
                    payload,
                    type,
                    created_at,
                    expires_at,
                    published_at,
                    publish_attempts,
                ) VALUES (
                    :id,
                    :payload,
                    :type,
                    :created_at,
                    :expires_at,
                    :published_at,
                    :publish_attempts,
                )
                """
            ).bindparams(bindparam('payload', type_=JSON))

            await self.conn.execute(
                query,
                {
                    'id': message.id,
                    'payload': message.payload.to_dict(),
                    'type': message.type,
                    'created_at': message.created_at,
                    'expires_at': message.expires_at,
                    'published_at': message.published_at,
                    'publish_attempts': message.publish_attempts,
                },
            )

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to create message',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e
