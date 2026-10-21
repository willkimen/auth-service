from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


@lru_cache
def create_engine(database_uri: str) -> AsyncEngine:
    """
    Creates and caches an asynchronous SQLAlchemy engine for the given
    database connection URI.

    Args:
        `database_uri` (`str`):
            - Database connection URI.

    Returns:
        `AsyncEngine`:
            - Cached asynchronous SQLAlchemy engine used for database
              operations.
    """
    return create_async_engine(database_uri)
