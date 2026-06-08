from unittest.mock import AsyncMock, MagicMock

import pytest

from adapters.outputs.repositories.unit_of_work import SqlAlchemyUnitOfWork


def engine_mock(
    engine: AsyncMock, connection: AsyncMock, transaction: AsyncMock
):
    engine.connect = AsyncMock(return_value=connection)

    connection.begin = AsyncMock(return_value=transaction)
    connection.close = AsyncMock()

    transaction.commit = AsyncMock()
    transaction.rollback = AsyncMock()


async def test_transaction_is_committed_successfully_when_no_error_occurs():
    # arrange
    engine = MagicMock()
    connection = MagicMock()
    transaction = MagicMock()

    engine_mock(engine, connection, transaction)

    uow = SqlAlchemyUnitOfWork(engine)

    # act
    # simulate not error
    async with uow:
        ...

    # assert
    transaction.rollback.assert_not_awaited()
    transaction.commit.assert_awaited_once()
    connection.close.assert_awaited_once()


async def test_transaction_is_rolled_back_successfully_when_an_error_occurs():
    # arrange
    engine = MagicMock()
    connection = MagicMock()
    transaction = MagicMock()

    engine_mock(engine, connection, transaction)

    uow = SqlAlchemyUnitOfWork(engine)

    # act and assert
    # simulete error
    with pytest.raises(RuntimeError):
        async with uow:
            raise RuntimeError()

    transaction.rollback.assert_awaited_once()
    connection.close.assert_awaited_once()
    transaction.commit.assert_not_awaited()
