import uuid

from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.user_repository import (
    PostgresUserRepository,
)
from domain.entities.user import User


async def test_should_return_user_when_public_id_exists(
    conn_rollback: AsyncConnection,
    user: User,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    await repository.create(user)

    # act
    actual_user = await repository.get_by_public_id(user.public_id)

    # assert
    assert user == actual_user


async def test_should_return_none_when_public_id_does_not_exist(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    # act
    actual_user = await repository.get_by_public_id(uuid.uuid4())

    # assert
    assert actual_user is None
