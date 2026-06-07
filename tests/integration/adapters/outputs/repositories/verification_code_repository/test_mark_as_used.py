from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.verification_code_repository import (
    PostgresVerificationCodeRepository,
)
from application.exceptions import InfrastructureError
from domain.entities.verification_code import VerificationCode

used = datetime.now(timezone.utc) + timedelta(minutes=1)


async def test_should_successfully_mark_a_verification_code_as_used(
    conn_rollback: AsyncConnection,
    verification_code: VerificationCode,
):
    # arrange
    repository = PostgresVerificationCodeRepository(conn_rollback)

    await repository.create(verification_code)

    verification_code.mark_as_used(used)

    # act
    await repository.mark_as_used(verification_code)

    # assert
    query = sqlalchemy.text(
        """
        SELECT used_at
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
    assert row.used_at == verification_code.used_at


async def test_update_fails_when_a_database_error_occurs(
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

    verification_code.mark_as_used(used)

    # act and assert
    with pytest.raises(InfrastructureError):
        await repository.mark_as_used(verification_code)

    monkeypatch.undo()

    # ensure NOTHING was update
    query = sqlalchemy.text(
        """
        SELECT used_at
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
    assert row.used_at is None
