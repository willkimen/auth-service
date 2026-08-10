import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self, engine: AsyncEngine):
        self._engine = engine

    async def cleanup_expired_verification_codes(self):
        async with self._engine.begin() as conn:
            try:
                await conn.execute(
                    text(
                        """
                        DELETE FROM verification_codes
                        WHERE expires_at <= NOW()
                        """
                    )
                )

            except SQLAlchemyError:
                logger.exception('Failed to cleanup expired verification codes')

    async def cleanup_used_verification_codes(self):
        async with self._engine.begin() as conn:
            try:
                await conn.execute(
                    text(
                        """
                        DELETE FROM verification_codes
                        WHERE used_at IS NOT NULL
                        """
                    )
                )

            except SQLAlchemyError:
                logger.exception('Failed to cleanup used verification codes')

    async def cleanup_revoked_refresh_tokens(self):
        async with self._engine.begin() as conn:
            try:
                await conn.execute(
                    text(
                        """
                        DELETE FROM refresh_tokens
                        WHERE revoked_at IS NOT NULL
                        """
                    )
                )

            except SQLAlchemyError:
                logger.exception('Failed to cleanup revoked refresh tokens')

    async def cleanup_expired_refresh_tokens(self):
        async with self._engine.begin() as conn:
            try:
                await conn.execute(
                    text(
                        """
                        DELETE FROM refresh_tokens
                        WHERE exp <= NOW()
                        """
                    )
                )

            except SQLAlchemyError:
                logger.exception('Failed to cleanup expired refresh tokens')

    async def cleanup(self):
        await self.cleanup_revoked_refresh_tokens()
        await self.cleanup_expired_refresh_tokens()
        await self.cleanup_used_verification_codes()
        await self.cleanup_expired_verification_codes()
