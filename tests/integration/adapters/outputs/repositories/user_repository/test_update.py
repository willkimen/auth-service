import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.user_repository import (
    PostgresUserRepository,
)
from application.exceptions import InfrastructureError
from domain.entities.user import User


async def test_should_successfully_update_a_user(
    conn_rollback: AsyncConnection,
    user: User,
    select_user_by_public_id: sqlalchemy.TextClause,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    await repository.create(user)

    user.mark_email_as_verified()
    user.deactivate()

    # act
    await repository.update(user)

    # assert
    row = (
        await conn_rollback.execute(
            select_user_by_public_id,
            {'public_id': user.public_id},
        )
    ).fetchone()

    assert row is not None
    assert row.email_verified is True
    assert row.is_active is False
    assert row.updated_at == user.updated_at


async def test_update_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection,
    monkeypatch,
    user: User,
    select_email_verified_column_by_public_id: sqlalchemy.TextClause,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    await repository.create(user)

    user.mark_email_as_verified()

    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Database error')

    monkeypatch.setattr(AsyncConnection, 'execute', mock_execute)

    # act and assert
    # ensure the infrastructure exception is raised
    with pytest.raises(InfrastructureError):
        await repository.update(user)

    # remove the mock to restore real database behavior
    monkeypatch.undo()

    # ensure the rollback kept the state intact

    row = (
        await conn_rollback.execute(
            select_email_verified_column_by_public_id,
            {'public_id': user.public_id},
        )
    ).fetchone()

    assert row is not None
    assert row.email_verified is False
