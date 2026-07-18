import pytest
import sqlalchemy
from sqlalchemy import TextClause, text
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


@pytest.fixture
async def clean_database(engine: AsyncEngine):
    """
    Cleans the database after each test.
    It must be called manually at the end of the tests.

    The fixture allows the test to run normally and, once it completes,
    removes all rows from the tables used by the application,
    resets their identity counters, and applies `CASCADE` to preserve
    referential integrity. This ensures that each test runs against
    a clean and isolated database state.
    """

    async def closure():
        async with engine.begin() as conn:
            await conn.execute(
                text("""
                TRUNCATE TABLE
                    users,
                    verification_codes,
                    messages,
                    refresh_tokens
                RESTART IDENTITY CASCADE;
            """)
            )

    return closure


@pytest.fixture
def select_user_by_public_id() -> TextClause:
    """
    Provides a reusable SQL query for retrieving a user by its `public_id`.
    """
    return sqlalchemy.text(
        """
        SELECT *
        FROM users
        WHERE public_id = :public_id
        """
    )
