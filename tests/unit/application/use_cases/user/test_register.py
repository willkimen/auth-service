import uuid
from dataclasses import fields
from datetime import datetime

import pytest

from application.dto.user_dto import UserPublicDTO
from application.exceptions import (
    EmailAlreadyUsedError,
    InfrastructureError,
    InfrastructureErrorCode,
)
from application.use_cases.user.register import RegisterUserUseCase
from domain.exceptions import InvalidEmailError, InvalidPasswordError
from unit.application.use_cases.user.types import RegisterUserDependencies

email_input = 'test@email.com'
password_input = 'PasswordTest12345!'


async def test_register_user_successfully(
    register_user_dependencies: RegisterUserDependencies,
):
    # arrange
    deps = register_user_dependencies
    user_case = RegisterUserUseCase(deps.hasher, deps.user_repo)

    # act
    result: UserPublicDTO = await user_case.execute(
        email_input, password_input
    )

    # assert
    deps.user_repo.exists_by_email.assert_awaited_once_with(email_input)
    deps.hasher.hash.assert_called_once_with(password_input)
    deps.user_repo.create.assert_awaited_once()

    assert isinstance(result.public_id, uuid.UUID)
    assert result.email == email_input
    assert isinstance(result.created_at, datetime)
    assert result.email_verified is False
    assert result.last_login_at is None

    assert {field.name for field in fields(result)} == {
        'public_id',
        'email',
        'created_at',
        'email_verified',
        'last_login_at',
    }


async def test_not_register_when_email_is_invalid(
    register_user_dependencies: RegisterUserDependencies,
):
    # arrange
    deps = register_user_dependencies
    use_case = RegisterUserUseCase(deps.hasher, deps.user_repo)

    invalid_email = 'testemail.com'

    # act assert
    with pytest.raises(InvalidEmailError):
        await use_case.execute(invalid_email, password_input)

    # assert
    deps.user_repo.exists_by_email.assert_not_awaited()
    deps.hasher.hash.assert_not_called()
    deps.user_repo.create.assert_not_awaited()


async def test_not_register_when_password_is_invalid(
    register_user_dependencies: RegisterUserDependencies,
):
    # arrange
    deps = register_user_dependencies
    use_case = RegisterUserUseCase(deps.hasher, deps.user_repo)

    invalid_password_input = 'invalidpassword'

    # act assert
    with pytest.raises(InvalidPasswordError):
        await use_case.execute(email_input, invalid_password_input)

    # assert
    deps.user_repo.exists_by_email.assert_not_awaited()
    deps.hasher.hash.assert_not_called()
    deps.user_repo.create.assert_not_awaited()


async def test_not_register_when_email_already_used(
    register_user_dependencies: RegisterUserDependencies,
):
    # arrange
    deps = register_user_dependencies

    deps.user_repo.exists_by_email.return_value = True
    use_case = RegisterUserUseCase(deps.hasher, deps.user_repo)

    # act assert
    with pytest.raises(EmailAlreadyUsedError):
        await use_case.execute(email_input, password_input)

    # assert
    deps.user_repo.exists_by_email.assert_awaited_once_with(email_input)
    deps.hasher.hash.assert_not_called()
    deps.user_repo.create.assert_not_awaited()


async def test_checking_email_availability_can_raise_infrastructure_error(
    register_user_dependencies: RegisterUserDependencies,
):
    # arrange
    deps = register_user_dependencies
    deps.user_repo.exists_by_email.side_effect = InfrastructureError(
        message='An unexpected error occurred while accessing the database.',
        code=InfrastructureErrorCode.DATABASE,
        cause=Exception(),
    )
    use_case = RegisterUserUseCase(deps.hasher, deps.user_repo)

    # act assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(email_input, password_input)

    # assert
    deps.user_repo.exists_by_email.assert_awaited_once_with(email_input)
    deps.hasher.hash.assert_not_called()
    deps.user_repo.create.assert_not_awaited()


async def test_hashing_password_can_raise_infrastructure_error(
    register_user_dependencies: RegisterUserDependencies,
):
    # arrange
    deps = register_user_dependencies
    deps.hasher.hash.side_effect = InfrastructureError(
        message='An unexpected error occurred while hashing password.',
        code=InfrastructureErrorCode.PASSWORD_HASHER,
        cause=Exception(),
    )
    use_case = RegisterUserUseCase(deps.hasher, deps.user_repo)

    # act assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(email_input, password_input)

    # assert
    deps.user_repo.exists_by_email.assert_awaited_once_with(email_input)
    deps.hasher.hash.assert_called_once_with(password_input)
    deps.user_repo.create.assert_not_awaited()


async def test_create_user_can_raise_infrastructure_error(
    register_user_dependencies: RegisterUserDependencies,
):
    # arrange
    deps = register_user_dependencies
    deps.user_repo.create.side_effect = InfrastructureError(
        message='An unexpected error occurred while accessing the database.',
        code=InfrastructureErrorCode.DATABASE,
        cause=Exception(),
    )
    use_case = RegisterUserUseCase(deps.hasher, deps.user_repo)

    # act assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(email_input, password_input)

    # assert
    deps.user_repo.exists_by_email.assert_awaited_once_with(email_input)
    deps.hasher.hash.assert_called_once_with(password_input)
    deps.user_repo.create.assert_awaited_once()
