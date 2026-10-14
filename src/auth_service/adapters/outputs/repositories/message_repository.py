import uuid
from typing import Sequence

from sqlalchemy import JSON, RowMapping, bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from auth_service.application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_types import MessageType
from auth_service.application.messages.payload import payload_from_dict


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
                    publish_attempts
                ) VALUES (
                    :id,
                    :payload,
                    :type,
                    :created_at,
                    :expires_at,
                    :published_at,
                    :publish_attempts
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

    async def find_pending_messages_by_type(
        self,
        types: Sequence[MessageType],
        limit: int = 100,
    ) -> list[Message]:
        """
        Retrieves unpublished messages matching the specified types.

        Args:
            types: Message types used to filter pending messages.

        Returns:
            Messages that have not been published, have not expired,
            and have remaining publication attempts.

        Raises:
            InfrastructureError:
                Raised when retrieving messages fails.
        """
        if not types:
            return []

        query = text(
            """
            SELECT
                id,
                payload,
                type,
                created_at,
                expires_at,
                published_at,
                publish_attempts,
            FROM messages
            WHERE published_at IS NULL
              AND type IN :types
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at ASC
            LIMIT :limit
            """
        ).bindparams(bindparam('types', expanding=True))

        try:
            result = await self.conn.execute(
                query,
                {
                    'types': [message_type.value for message_type in types],
                    'limit': limit,
                },
            )

            return [self._to_message(row) for row in result.mappings().all()]

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to retrieve pending messages',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e

    async def mark_as_published(self, message_id: uuid.UUID) -> None:
        """
        Marks a message as successfully published.

        Args:
            message_id: Unique identifier of the message to update.

        Raises:
            InfrastructureError:
                Raised when updating the message fails.
        """
        query = text(
            """
            UPDATE messages
            SET published_at = NOW()
            WHERE id = :id
              AND published_at IS NULL
            """
        )

        try:
            await self.conn.execute(query, {'id': message_id})

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to mark message as published',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e

    async def increment_publish_attempts(self, message_id: uuid.UUID) -> None:
        """
        Increments the publication attempt counter for a message.

        Args:
            message_id: Unique identifier of the message to update.

        Raises:
            InfrastructureError:
                Raised when updating the message fails.
        """
        query = text(
            """
            UPDATE messages
            SET publish_attempts = publish_attempts + 1
            WHERE id = :id
              AND published_at IS NULL
            """
        )

        try:
            await self.conn.execute(query, {'id': message_id})

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to increment publication attempts',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e

    @staticmethod
    def _to_message(row: RowMapping) -> Message:
        """Converts a database row into a Message instance."""
        try:
            message_type = MessageType(row['type'])
            payload = payload_from_dict(message_type, row['payload'])

            return Message(
                id=row['id'],
                payload=payload,
                type=message_type,
                created_at=row['created_at'],
                expires_at=row['expires_at'],
                published_at=row['published_at'],
                publish_attempts=row['publish_attempts'],
            )

        except (ValueError, TypeError, KeyError) as e:
            raise InfrastructureError(
                message='Failed to reconstruct message from database row',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e
