import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.verification_code_repository import (
    PostgresVerificationCodeRepository,
)
from application.exceptions import InfrastructureError
from domain.entities.verification_code import VerificationCode


async def test_should_successfully_create_a_verification_code(
    conn_rollback: AsyncConnection,
    verification_code: VerificationCode,
):
    # arrange
    repository = PostgresVerificationCodeRepository(conn_rollback)

    # act
    await repository.create(verification_code)

    # assert
    query = sqlalchemy.text(
        """
        SELECT
            code,
            user_public_id,
            type,
            created_at,
            expires_at,
            used_at,
            payload
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
    assert row.code == verification_code.code.value
    assert row.user_public_id == verification_code.user_public_id
    assert row.type == verification_code.type.value
    assert row.created_at == verification_code.created_at
    assert row.expires_at == verification_code.expires_at
    assert row.used_at == verification_code.used_at
    assert row.payload == verification_code.payload


async def test_creation_fails_when_a_database_error_occurs(
    conn_rollback: AsyncConnection,
    monkeypatch,
    verification_code: VerificationCode,
):
    # arrange
    repository = PostgresVerificationCodeRepository(conn_rollback)

    async def mock_execute(*args, **kwargs):
        raise SQLAlchemyError('Database error')

    monkeypatch.setattr(
        AsyncConnection,
        'execute',
        mock_execute,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await repository.create(verification_code)

    monkeypatch.undo()

    # ensure NOTHING was persisted
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

    assert row is None
