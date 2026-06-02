import uuid
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from application.exceptions import InfrastructureError, InfrastructureErrorCode


class RefreshTokenRepository:
    def __init__(self, conn: AsyncConnection):
        self.conn = conn

    async def save_refresh(
        self,
        sub: uuid.UUID,
        jti: str,
        expires_at: datetime,
    ) -> None:
        """Stores a refresh token."""
        try:
            query = text("""
                INSERT INTO refresh_token (jti, sub, exp)
                VALUES (:jti, :sub, :expires_at)
            """)

            await self.conn.execute(
                query,
                {'jti': jti, 'sub': sub, 'expires_at': expires_at},
            )
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Token creating operation failed',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e

    async def revoke_all_refreshes(self, sub: uuid.UUID) -> None:
        """Revokes all refresh tokens for a subject."""
        try:
            query = text("""
                UPDATE refresh_token
                SET revoked_at = NOW()
                WHERE sub = :sub AND revoked_at IS NULL
            """)

            await self.conn.execute(query, {'sub': sub})
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Operation to revoke all user refreshes failed',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e

    async def revoke_refresh(self, jti: str) -> None:
        """Revoke a specific refresh token."""
        try:
            query = text("""
                UPDATE refresh_token
                SET revoked_at = NOW()
                WHERE jti = :jti AND revoked_at IS NULL
            """)

            await self.conn.execute(query, {'jti': jti})
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Operation to revoke user refresh failed',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e

    async def exists(self, jti: str) -> bool:
        """Checks if a token exists."""
        try:
            query = text("""
                SELECT EXISTS (
                    SELECT 1 FROM refresh_token WHERE jti = :jti
                )
            """)

            result = await self.conn.execute(query, {'jti': jti})
            return bool(result.scalar())
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message=(
                    'Operation to verify the existence of the token failed'
                ),
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e

    async def is_revoked(self, jti: str) -> bool:
        """Checks if a token is revoked."""
        try:
            query = text("""
                SELECT EXISTS (
                    SELECT 1
                    FROM refresh_token
                    WHERE jti = :jti AND (
                        revoked_at IS NOT NULL
                    )
                )
            """)

            result = await self.conn.execute(query, {'jti': jti})
            return bool(result.scalar())
        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Operation to check if the token has expired failed',
                code=InfrastructureErrorCode.DATABASE,
                cause=e,
            ) from e
