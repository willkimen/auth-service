from typing import Sequence

from sqlalchemy import JSON, RowMapping, bindparam, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from auth_service.application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)
from auth_service.application.messages.message import (
    Message,
    MessageFailureCode,
    MessageStatus,
)
from auth_service.application.messages.message_enums import MessageType
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
        query = text(
            """
            INSERT INTO messages (
                id,
                payload,
                type,
                status,
                created_at,
                expires_at,
                published_at,
                publish_attempts,
                failure_code,
                failure_reason
            ) VALUES (
                :id,
                :payload,
                :type,
                :status,
                :created_at,
                :expires_at,
                :published_at,
                :publish_attempts,
                :failure_code,
                :failure_reason
            )
            """
        ).bindparams(bindparam('payload', type_=JSON))

        try:
            await self.conn.execute(
                query,
                {
                    'id': message.id,
                    'payload': message.payload.to_dict(),
                    'type': message.type.value,
                    'status': message.status.value,
                    'created_at': message.created_at,
                    'expires_at': message.expires_at,
                    'published_at': message.published_at,
                    'publish_attempts': message.publish_attempts,
                    'failure_code': (
                        message.failure_code.value
                        if message.failure_code is not None
                        else None
                    ),
                    'failure_reason': message.failure_reason,
                },
            )

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to create message',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e

    async def update(self, message: Message) -> None:
        """Updates the publication state of an existing message."""
        query = text("""
            UPDATE messages
            SET
                status = :status,
                published_at = :published_at,
                publish_attempts = :publish_attempts,
                failure_code = :failure_code,
                failure_reason = :failure_reason
            WHERE id = :id
        """)

        try:
            await self.conn.execute(
                query,
                {
                    'id': message.id,
                    'status': message.status.value,
                    'published_at': message.published_at,
                    'publish_attempts': message.publish_attempts,
                    'failure_code': (
                        message.failure_code.value
                        if message.failure_code is not None
                        else None
                    ),
                    'failure_reason': message.failure_reason,
                },
            )

        except SQLAlchemyError as exc:
            raise InfrastructureError(
                message='Failed to update message.',
                code=InfrastructureErrorCode.DATABASE_ERROR,
            ) from exc

    async def find_pending_messages_by_type(
        self,
        types: Sequence[MessageType],
        limit: int = 100,
    ) -> list[Message]:
        """
        Retrieves pending, non-expired messages matching the specified types.

        Args:
            types: Message types used to filter pending messages.
            limit: Maximum number of messages to retrieve.

        Returns:
            Messages awaiting publication that have not expired.

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
                status,
                created_at,
                expires_at,
                published_at,
                publish_attempts,
                failure_code,
                failure_reason
            FROM messages
            WHERE status = :status
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
                    'status': MessageStatus.PENDING.value,
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

    @staticmethod
    def _to_message(row: RowMapping) -> Message:
        """Converts a database row into a Message instance."""
        try:
            message_type = MessageType(row['type'])
            payload = payload_from_dict(message_type, row['payload'])

            failure_code_value = row['failure_code']
            failure_code = (
                MessageFailureCode(failure_code_value)
                if failure_code_value is not None
                else None
            )

            return Message(
                id=row['id'],
                payload=payload,
                type=message_type,
                status=MessageStatus(row['status']),
                created_at=row['created_at'],
                expires_at=row['expires_at'],
                published_at=row['published_at'],
                publish_attempts=row['publish_attempts'],
                failure_code=failure_code,
                failure_reason=row['failure_reason'],
            )

        except (ValueError, TypeError, KeyError) as e:
            raise InfrastructureError(
                message='Failed to reconstruct message from database row',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e
