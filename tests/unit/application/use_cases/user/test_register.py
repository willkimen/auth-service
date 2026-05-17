import uuid
from dataclasses import dataclass, fields
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from application.dtos.user_dto import UserPublicDTO
from application.exceptions import (
    EmailAlreadyUsedError,
    InfrastructureError,
    InfrastructureErrorCode,
)
from application.ports.output import (
    HasherPort,
    UserRepositoryPort,
)
from application.use_cases.user.register import RegisterUserUseCase
from domain.entities.user import User
from domain.exceptions import InvalidEmailError, InvalidPasswordError
from domain.value_objects.password import PasswordHash

email_input = 'test@email.com'
password_input = 'PasswordTest12345!'


async def test_register_user_flow_successfully():
    """
    Verifies if the user creation flow in the system is correctly chained.

    Checks:
        - If methods were called with the correct arguments.
        - If it correctly returns an object with secure user data.
    """
    mocks: DependeciesMocked = mock_dependecies_factory()
    use_case = RegisterUserUseCase(mocks.hasher, mocks.user_repo)

    # act
    result: UserPublicDTO = await use_case.execute(email_input, password_input)

    # assert that the returned fields contain the correct state.
    assert isinstance(result.public_id, uuid.UUID)
    assert result.email == email_input
    assert isinstance(result.created_at, datetime)
    assert result.email_verified is False
    assert result.last_login_at is None

    # Assert that the returned fields are the following:
    assert {field.name for field in fields(result)} == {
        'public_id',
        'email',
        'created_at',
        'email_verified',
        'last_login_at',
    }

    # assert was called
    mocks.user_repo.exists_by_email.assert_called_once_with(email_input)
    mocks.hasher.hash.assert_called_once_with(password_input)
    mocks.user_repo.create.assert_called_once()

    # assert that user_repo.create() was called with correct arguments
    # in this case, the received argument must be a User instance with
    # the following state:
    user_arg: User = mocks.user_repo.create.call_args[0][0]
    assert isinstance(user_arg.public_id, uuid.UUID)
    assert isinstance(user_arg.hash_password, PasswordHash)
    # the returned email must have the same value as the input email.
    assert user_arg.email.value == email_input
    # as a newly created user, they must be unverified and active.
    assert user_arg.email_verified is False
    assert user_arg.is_active is True
    assert isinstance(user_arg.created_at, datetime)
    assert user_arg.updated_at == user_arg.created_at
    assert user_arg.last_login_at is None


async def test_not_register_when_email_is_invalid():
    mocks: DependeciesMocked = mock_dependecies_factory()
    use_case = RegisterUserUseCase(mocks.hasher, mocks.user_repo)
    invalid_email = 'testemail.com'

    # act and assert
    with pytest.raises(InvalidEmailError):
        await use_case.execute(invalid_email, password_input)

    # assert was not called
    mocks.user_repo.exists_by_email.assert_not_called()
    mocks.hasher.hash.assert_not_called()
    mocks.user_repo.create.assert_not_called()


async def test_not_register_when_password_is_invalid():
    mocks: DependeciesMocked = mock_dependecies_factory()
    use_case = RegisterUserUseCase(mocks.hasher, mocks.user_repo)
    invalid_password_input = 'invalidpassword'

    # act and assert
    with pytest.raises(InvalidPasswordError):
        await use_case.execute(email_input, invalid_password_input)

    # assert was not called
    mocks.user_repo.exists_by_email.assert_not_called()
    mocks.hasher.hash.assert_not_called()
    mocks.user_repo.create.assert_not_awaited()


async def test_not_register_when_email_already_used():
    """
    Test if the flow is aborted when the user is already verified.
    Verified users do not need to be verified again.
    """
    mocks: DependeciesMocked = mock_dependecies_factory()
    mocks.user_repo.exists_by_email.return_value = True
    use_case = RegisterUserUseCase(mocks.hasher, mocks.user_repo)

    # act and assert
    with pytest.raises(EmailAlreadyUsedError):
        await use_case.execute(email_input, password_input)

    # assert was called
    mocks.user_repo.exists_by_email.assert_called_once()

    # assert was not called
    mocks.hasher.hash.assert_not_called()
    mocks.user_repo.create.assert_not_called()


async def test_checking_email_availability_can_raise_infrastructure_error():
    """
    Test if an unexpected infrastructure layer (output adapter) error
    is raised when checking user existence, aborting the flow.
    """
    mocks: DependeciesMocked = mock_dependecies_factory()
    mocks.user_repo.exists_by_email.side_effect = InfrastructureError(
        message='An unexpected error occurred while accessing the database.',
        code=InfrastructureErrorCode.DATABASE,
        cause=Exception(),
    )
    use_case = RegisterUserUseCase(mocks.hasher, mocks.user_repo)

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(email_input, password_input)

    # assert was called
    mocks.user_repo.exists_by_email.assert_called_once_with(email_input)

    # assert was not called
    mocks.hasher.hash.assert_not_called()
    mocks.user_repo.create.assert_not_awaited()


async def test_hashing_password_can_raise_infrastructure_error():
    """
    Test if an unexpected infrastructure layer (output adapter) error
    is raised when hashing the password, aborting the flow.
    """
    mocks: DependeciesMocked = mock_dependecies_factory()
    mocks.hasher.hash.side_effect = InfrastructureError(
        message='An unexpected error occurred while hashing password.',
        code=InfrastructureErrorCode.PASSWORD_HASHER,
        cause=Exception(),
    )
    use_case = RegisterUserUseCase(mocks.hasher, mocks.user_repo)

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(email_input, password_input)

    # assert was called
    mocks.user_repo.exists_by_email.assert_called_once_with(email_input)
    mocks.hasher.hash.assert_called_once_with(password_input)

    # assert was not called
    mocks.user_repo.create.assert_not_called()


async def test_create_user_can_raise_infrastructure_error():
    """
    Test if an unexpected infrastructure layer (output adapter) error
    is raised when trying to create the user in the database.
    """
    mocks: DependeciesMocked = mock_dependecies_factory()
    mocks.user_repo.create.side_effect = InfrastructureError(
        message='An unexpected error occurred while accessing the database.',
        code=InfrastructureErrorCode.DATABASE,
        cause=Exception(),
    )
    use_case = RegisterUserUseCase(mocks.hasher, mocks.user_repo)

    # act assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(email_input, password_input)

    # assert was called
    mocks.user_repo.exists_by_email.assert_called_once_with(email_input)
    mocks.hasher.hash.assert_called_once_with(password_input)
    mocks.user_repo.create.assert_called_once()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies of the use
    case.
    """

    hasher: Mock
    user_repo: AsyncMock


def mock_dependecies_factory() -> DependeciesMocked:
    """
    Return the mocked dependencies of the use case.

    Creates and configures mock instances for the hasher and user
    repository ports with default successful return values.
    """
    hasher = Mock(spec=HasherPort)
    hasher.hash.return_value = 'hashed-password'

    user_repo = AsyncMock(spec=UserRepositoryPort)
    # by default, it returns False, meaning no user exists for this email.
    user_repo.exists_by_email.return_value = False
    user_repo.create.return_value = None

    return DependeciesMocked(
        hasher=hasher,
        user_repo=user_repo,
    )
