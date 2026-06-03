import uuid
from datetime import datetime, timezone

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.user.user_repository import (
    PostgresUserRepository,
)
from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


async def test_should_successfully_create_a_user(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    user = User(
        public_id=uuid.uuid4(),
        email=Email('john@example.com'),
        hash_password=PasswordHash('$2b$12$hashedpassword'),
        email_verified=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )

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
