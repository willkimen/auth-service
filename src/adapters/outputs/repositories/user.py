import uuid

from sqlalchemy import CursorResult, Row, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.models import UserRowMapper
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
)
from domain.entities.user import User
from domain.exceptions import DomainError


class PostgresUserRepository:
    """Defines persistence operations for User entities."""

    def __init__(self, conn: AsyncConnection):
        self.conn = conn

    async def create(self, user: User) -> None:
        """Persists a new user record.

        Raises:
            InfrastructureError:
                If database insertion fails or is unavailable.
        """
        try:
            query = text(
                """
                INSERT INTO users (
                    public_id,
                    email,
                    hash_password,
                    email_verified,
                    is_active,
                    created_at,
                    updated_at,
                    last_login_at
                ) VALUES (
                    :public_id,
                    :email,
                    :hash_password,
                    :email_verified,
                    :is_active,
                    :created_at,
                    :updated_at,
                    :last_login_at
                )
                """
            )

            await self.conn.execute(
                query,
                {
                    'public_id': user.public_id,
                    'email': user.email.value,
                    'hash_password': user.hash_password.value,
                    'email_verified': user.email_verified,
                    'is_active': user.is_active,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at,
                    'last_login_at': user.last_login_at,
                },
            )

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to create user',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e

    async def update(self, user: User) -> None:
        """Updates an existing user record.

        Raises:
            InfrastructureError:
                If database update operation fails.
        """
        try:
            query = text(
                """
                UPDATE users
                SET
                    email = :email,
                    hash_password = :hash_password,
                    email_verified = :email_verified,
                    is_active = :is_active,
                    updated_at = :updated_at,
                    last_login_at = :last_login_at
                WHERE public_id = :public_id
                """
            )

            await self.conn.execute(
                query,
                {
                    'public_id': user.public_id,
                    'email': user.email.value,
                    'hash_password': user.hash_password.value,
                    'email_verified': user.email_verified,
                    'is_active': user.is_active,
                    'updated_at': user.updated_at,
                    'last_login_at': user.last_login_at,
                },
            )
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='User update operation failed',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e

    async def delete(self, public_id: uuid.UUID) -> None:
        """Deletes a user by public identifier.

        Raises:
            InfrastructureError:
                If delete operation fails in the database.
        """
        try:
            query = text(
                """
                DELETE FROM users
                WHERE public_id = :public_id
                """
            )

            await self.conn.execute(
                query,
                {'public_id': public_id},
            )
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='User delete operation failed',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e

    async def get_by_email(self, email: str) -> User | None:
        """Retrieves a user by email.

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
                SELECT * FROM users
                WHERE email = :email
                """
            )

            result: CursorResult = await self.conn.execute(
                query,
                {'email': email},
            )

            user_row: Row | None = result.one_or_none()
            if user_row is None:
                return None

            return UserRowMapper.to_domain(user_row)

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='User retrieval operation failed',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e
        except (DomainError, ValueError, TypeError, AttributeError) as e:
            raise CorruptedPersistenceStateError(cause=e)

    async def get_by_public_id(self, public_id: uuid.UUID) -> User | None:
        """Retrieves a user by public identifier.

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
                SELECT * FROM users
                WHERE public_id = :public_id
                """
            )

            result: CursorResult = await self.conn.execute(
                query,
                {'public_id': public_id},
            )

            user_row: Row | None = result.one_or_none()
            if user_row is None:
                return None

            return UserRowMapper.to_domain(user_row)

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='User retrieval operation failed',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e
        except (DomainError, ValueError, TypeError, AttributeError) as e:
            raise CorruptedPersistenceStateError(cause=e)

    async def exists_by_email(self, email: str) -> bool:
        """Checks if a user exists by email.

        Raises:
            InfrastructureError:
                If database check fails.
        """
        try:
            query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM users WHERE email = :email
                )
            """)

            result = await self.conn.execute(query, {'email': email})
            return bool(result.scalar())
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message=(
                    'Operation to verify the existence of the user failed'
                ),
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e
