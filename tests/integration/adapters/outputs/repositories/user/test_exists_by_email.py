from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.user import PostgresUserRepository
from domain.entities.user import User


async def test_should_return_true_when_user_exists_by_email(
    conn_rollback: AsyncConnection,
    user: User,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    await repository.create(user)

    # act
    actual = await repository.exists_by_email(user.email.value)

    # assert
    assert actual is True


async def test_should_return_false_when_user_does_not_exist_by_email(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresUserRepository(conn_rollback)

    # act
    actual = await repository.exists_by_email('nonexistent@example.com')

    # assert
    assert actual is False
