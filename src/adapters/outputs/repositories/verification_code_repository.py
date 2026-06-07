import uuid

from sqlalchemy import CursorResult, Row, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.models import VerificationCodeRowMapper
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
)
from domain.entities.verification_code import VerificationCode
from domain.exceptions import DomainError


class PostgresVerificationCodeRepository:
    """Defines persistence operations for verification codes."""

    def __init__(self, conn: AsyncConnection):
        self.conn = conn

    async def create(self, verification_code: VerificationCode) -> None:
        """Persists a verification code.

        Raises:
            InfrastructureError:
                If database insert fails.
        """
        try:
            query = text(
                """
                INSERT INTO verification_codes (
                    code,
                    user_public_id,
                    type,
                    created_at,
                    expires_at,
                    used_at,
                    payload
                ) VALUES (
                    :code,
                    :user_public_id,
                    :type,
                    :created_at,
                    :expires_at,
                    :used_at,
                    :payload
                )
                """
            )

            await self.conn.execute(
                query,
                {
                    'code': verification_code.code.value,
                    'user_public_id': verification_code.user_public_id,
                    'type': verification_code.type.value,
                    'created_at': verification_code.created_at,
                    'expires_at': verification_code.expires_at,
                    'used_at': verification_code.used_at,
                    'payload': verification_code.payload,
                },
            )

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to create verification code',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e

    async def mark_as_used(self, verification_code: VerificationCode) -> None:
        """Marks a verification code as used in the database.

        Raises:
            InfrastructureError: If database update fails.
        """
        try:
            query = text(
                """
                UPDATE verification_codes
                SET
                    used_at = :used_at
                WHERE code = :code AND user_public_id = :user_public_id
                """
            )

            await self.conn.execute(
                query,
                {
                    'code': verification_code.code.value,
                    'user_public_id': verification_code.user_public_id,
                    'used_at': verification_code.used_at,
                },
            )
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Mark verification code as used operation failed',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e

    async def get_by_user_id_and_code(
        self,
        user_public_id: uuid.UUID,
        code: str,
    ) -> VerificationCode | None:
        """Retrieves a verification code by user and code value.

        Raises:
            CorruptedPersistenceStateError:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            InfrastructureError:
                If query execution fails.
        """
        try:
            query = text(
                """
                SELECT * FROM verification_codes
                WHERE code = :code AND user_public_id = :user_public_id
                """
            )

            result: CursorResult = await self.conn.execute(
                query,
                {'code': code, 'user_public_id': user_public_id},
            )

            code_row: Row | None = result.one_or_none()
            if code_row is None:
                return None

            return VerificationCodeRowMapper.to_domain(code_row)

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Verification code retrieval operation failed',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e
        except (DomainError, ValueError, TypeError, AttributeError) as e:
            raise CorruptedPersistenceStateError(cause=e)

    async def delete_all(self, user_public_id: uuid.UUID):
        """Deletes all verification codes for a user.

        Raises:
            InfrastructureError:
                If delete operation fails.
        """
        try:
            query = text(
                """
                DELETE FROM verification_codes
                WHERE user_public_id = :user_public_id
                """
            )

            await self.conn.execute(
                query,
                {'user_public_id': user_public_id},
            )
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Verification code delete operation failed',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e
