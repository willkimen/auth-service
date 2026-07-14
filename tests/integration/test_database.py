import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncConnection


async def test_database_connection_and_schema(conn_rollback: AsyncConnection):
    """Ensures the database is connected and schemas are initialized."""
    # 1. Tests basic connectivity
    result = await conn_rollback.execute(sqlalchemy.text('SELECT 1;'))
    assert result.scalar() == 1

    # 2. Automatically inspects if any tables were loaded by Docker
    # We define a small internal function to execute the sync inspection
    def get_tables(sync_conn):
        inspector = sqlalchemy.inspect(sync_conn)
        return inspector.get_table_names()

    # run_sync passes a temporary sync connection to our function
    tables = await conn_rollback.run_sync(get_tables)

    # Ensures that at least one table exists (your schema is not empty)
    assert len(tables) > 0
