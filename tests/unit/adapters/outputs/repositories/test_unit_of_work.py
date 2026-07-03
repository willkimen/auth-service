from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import SQLAlchemyError

from adapters.outputs.repositories.unit_of_work import SqlAlchemyUnitOfWork
from application.exceptions import InfrastructureError, InfrastructureErrorCode


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


async def test_raise_infrastructure_error_when_connection_creation_fails():
    # arrange
    engine = MagicMock()
    engine.connect = AsyncMock(side_effect=SQLAlchemyError('connection error'))

    uow = SqlAlchemyUnitOfWork(engine)

    # act / assert
    with pytest.raises(InfrastructureError) as exc:
        async with uow:
            ...

    assert exc.value.code == InfrastructureErrorCode.DATABASE_ERROR
    assert isinstance(exc.value.__cause__, SQLAlchemyError)


async def test_raise_infrastructure_error_when_transaction_start_fails():
    # arrange
    engine = MagicMock()
    connection = MagicMock()

    engine.connect = AsyncMock(return_value=connection)

    connection.begin = AsyncMock(side_effect=SQLAlchemyError('begin error'))

    uow = SqlAlchemyUnitOfWork(engine)

    # act and assert
    with pytest.raises(InfrastructureError) as exc:
        async with uow:
            ...

    assert exc.value.code == InfrastructureErrorCode.DATABASE_ERROR
    assert isinstance(exc.value.__cause__, SQLAlchemyError)


async def test_raise_infrastructure_error_when_commit_fails():
    # arrange
    engine = MagicMock()
    connection = MagicMock()
    transaction = MagicMock()

    engine_mock(engine, connection, transaction)

    transaction.commit.side_effect = SQLAlchemyError('commit error')

    uow = SqlAlchemyUnitOfWork(engine)

    # act and assert
    with pytest.raises(InfrastructureError) as exc:
        async with uow:
            ...

    connection.close.assert_awaited_once()

    assert exc.value.code == InfrastructureErrorCode.DATABASE_ERROR
    assert isinstance(exc.value.__cause__, SQLAlchemyError)


async def test_raise_infrastructure_error_when_rollback_fails():
    # arrange
    engine = MagicMock()
    connection = MagicMock()
    transaction = MagicMock()

    engine_mock(engine, connection, transaction)

    transaction.rollback.side_effect = SQLAlchemyError('rollback error')

    uow = SqlAlchemyUnitOfWork(engine)

    # act and assert
    with pytest.raises(InfrastructureError) as exc:
        async with uow:
            raise RuntimeError()

    connection.close.assert_awaited_once()

    assert exc.value.code == InfrastructureErrorCode.DATABASE_ERROR
    assert isinstance(exc.value.__cause__, SQLAlchemyError)
