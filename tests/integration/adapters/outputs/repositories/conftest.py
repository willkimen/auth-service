import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

DATABASE_URL = 'postgresql+psycopg://test:test@localhost:5432/test-auth'


@pytest.fixture(scope='session')
async def engine():
    "Connects to the fixed database initialized by the Docker container."
    db_engine: AsyncEngine = create_async_engine(DATABASE_URL)

    yield db_engine

    # Explicitly disposes of the connection pool after the session ends
    await db_engine.dispose()


@pytest.fixture
async def conn_rollback(engine: AsyncEngine):
    "Provides a connection and rolls back all changes after the test."
    async with engine.connect() as connection:
        # We start a transaction explicitly
        transaction = await connection.begin()

        yield connection

        # This guarantees a physical rollback after the test finishes,
        # regardless of whether the test passed or failed.
        await transaction.rollback()
