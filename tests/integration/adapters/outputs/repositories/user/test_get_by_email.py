from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.user import PostgresUserRepository
from domain.entities.user import User


async def test_should_return_user_when_email_exists(
    conn_rollback: AsyncConnection,
    user: User,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)
    await repository.create(user)

    # act
    actual_user: User | None = await repository.get_by_email(user.email.value)

    # assert
    assert user == actual_user


async def test_should_return_none_when_email_does_not_exist(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    # act
    actual_user: User | None = await repository.get_by_email(
        'nonexists@email.com'
    )

    # assert
    assert actual_user is None
