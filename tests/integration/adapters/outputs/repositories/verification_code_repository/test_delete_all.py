import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.verification_code_repository import (
    PostgresVerificationCodeRepository,
)
from application.exceptions import InfrastructureError
from domain.entities.verification_code import VerificationCode


async def test_should_successfully_delete_all_verification_codes_for_a_user(
    conn_rollback: AsyncConnection,
    verification_code: VerificationCode,
):
    # arrange
    repository = PostgresVerificationCodeRepository(conn_rollback)

    await repository.create(verification_code)

    # act
    await repository.delete_all(verification_code.user_public_id)

    # assert
    query = sqlalchemy.text(
        """
        SELECT code
        FROM verification_codes
        WHERE user_public_id = :user_public_id
        """
    )

    row = (
        await conn_rollback.execute(
            query,
            {'user_public_id': (verification_code.user_public_id)},
        )
    ).fetchone()

    assert row is None


async def test_delete_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection,
    monkeypatch,
    verification_code: VerificationCode,
):
    # arrange
    repository = PostgresVerificationCodeRepository(conn_rollback)

    await repository.create(verification_code)

    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Database error')

    monkeypatch.setattr(
        AsyncConnection,
        'execute',
        mock_execute,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await repository.delete_all(verification_code.user_public_id)

    monkeypatch.undo()

    # ensure nothing was deleted
    query = sqlalchemy.text(
        """
        SELECT code
        FROM verification_codes
        WHERE code = :code
        """
    )

    row = (
        await conn_rollback.execute(
            query,
            {'code': verification_code.code.value},
        )
    ).fetchone()

    assert row is not None
