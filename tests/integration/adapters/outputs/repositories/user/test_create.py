import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.user import PostgresUserRepository
from application.exceptions import InfrastructureError
from domain.entities.user import User


async def test_should_successfully_create_a_user(
    conn_rollback: AsyncConnection,
    user: User,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    # act
    await repository.create(user)

    # assert
    query = sqlalchemy.text(
        """
        SELECT
            public_id,
            email,
            hash_password,
            email_verified,
            is_active,
            created_at,
            updated_at,
            last_login_at
        FROM users
        WHERE public_id = :public_id
        """
    )

    row = (
        await conn_rollback.execute(
            query,
            {'public_id': user.public_id},
        )
    ).fetchone()

    assert row is not None

    assert row.public_id == user.public_id
    assert row.email == user.email.value
    assert row.hash_password == user.hash_password.value
    assert row.email_verified is user.email_verified
    assert row.is_active is user.is_active
    assert row.created_at == user.created_at
    assert row.updated_at == user.updated_at
    assert row.last_login_at is None


async def test_creation_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection,
    monkeypatch,
    user: User,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Database error')

    monkeypatch.setattr(AsyncConnection, 'execute', mock_execute)

    # act and assert
    # ensure the infrastructure exception is raised
    with pytest.raises(InfrastructureError):
        await repository.create(user)

    # remove the mock to restore real database behavior
    monkeypatch.undo()

    # ensure NOTHING was persisted in the real database
    query = sqlalchemy.text(
        """
        SELECT public_id
        FROM users
        WHERE public_id = :public_id
        """
    )

    result = await conn_rollback.execute(
        query,
        {'public_id': user.public_id},
    )

    row = result.fetchone()

    # The record must not exist due to the automatic rollback
    assert row is None
