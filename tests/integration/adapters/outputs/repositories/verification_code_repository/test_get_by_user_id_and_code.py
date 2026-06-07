import uuid

from sqlalchemy.ext.asyncio import AsyncConnection

from adapters.outputs.repositories.verification_code_repository import (
    PostgresVerificationCodeRepository,
)
from domain.entities.verification_code import VerificationCode


async def test_should_return_verification_code_when_it_exists(
    conn_rollback: AsyncConnection,
    verification_code: VerificationCode,
):
    # arrange
    repository = PostgresVerificationCodeRepository(conn_rollback)

    await repository.create(verification_code)

    # act
    actual_code = await repository.get_by_user_id_and_code(
        user_public_id=verification_code.user_public_id,
        code=verification_code.code.value,
    )

    # assert
    assert verification_code == actual_code


async def test_should_return_none_when_verification_code_does_not_exist(
    conn_rollback: AsyncConnection,
):
    # arrange
    repository = PostgresVerificationCodeRepository(conn_rollback)

    # act
    actual_code = await repository.get_by_user_id_and_code(
        user_public_id=uuid.uuid4(),
        code='123456',
    )

    # assert
    assert actual_code is None
