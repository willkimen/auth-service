import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import AsyncMock

import pytest

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidTokenError,
    InvalidTokenErrorCode,
    InvalidTokenTypeError,
    PasswordMismatchError,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import PasswordChangedPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    HasherPort,
    MessageRepositoryPort,
    TokenManagerPort,
    TokenRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.change_password import ChangePasswordUseCase
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    DomainError,
    InactiveUserError,
    InvalidPasswordError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)

token = 'token'
code = '123456'
new_password = 'Password@123'
new_password_confirmation = 'Password@123'
hashed_password = 'hashed-password'
jti = 'jti'


async def test_change_password_successfully(
    active_user: User,
    create_unused_code,
):
    """
    Test if the complete password change flow executes successfully.

    Success is verified by checking:
    - password validation and hashing
    - token validation
    - verification code validation and consumption
    - password update
    - refresh token revocation
    - notification message persistence

    args:
        active_user (User):
            Active user used during the password change flow.

        create_unused_code:
            Factory fixture that creates a valid unused verification code.
    """
    unused_code = create_unused_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=unused_code,
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )
    # act
    await use_case.execute(
        access=token,
        code=unused_code.code.value,
        new_password=new_password,
        new_password_confirmation=new_password,
    )

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.hasher.hash.assert_called_once_with(new_password)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once_with(
        active_user.public_id,
        unused_code.code.value,
    )
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.code_repo.update.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()

    # assert user_repo.update() arguments
    user_args: User = mocks.uow.user_repo.update.call_args[0][0]
    assert user_args.public_id == active_user.public_id
    assert user_args.hash_password.value == mocks.hasher.hash.return_value
    assert user_args.updated_at >= active_user.updated_at

    # assert code_repo.update() arguments
    verification_code_args: VerificationCode = (
        mocks.uow.code_repo.update.call_args[0][0]
    )
    assert verification_code_args.user_public_id == active_user.public_id
    assert verification_code_args.code.value == unused_code.code.value
    assert verification_code_args.type == CodeType.CHANGE_PASSWORD
    assert verification_code_args.used_at is not None

    # assert message_repo.create() arguments
    message_args: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_args.type == MessageType.NOTIFICATION_PASSWORD_CHANGED

    payload_args: PasswordChangedPayload = message_args.payload
    assert payload_args.to == active_user.email.value
    assert payload_args.subject == 'Your password was changed'


async def test_password_change_not_performed_when_password_is_invalid(
    active_user: User,
):
    """
    The password change flow is aborted when the provided password
    does not satisfy password policy requirements.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    invalid_password = '123'

    # act and assert
    with pytest.raises(InvalidPasswordError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=invalid_password,
            new_password_confirmation=invalid_password,
        )

    # assert was not called
    mocks.hasher.hash.assert_not_called()
    mocks.token_manager.validate.assert_not_called()
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_not_performed_when_password_confirmation_differs(
    active_user: User,
):
    """
    The password change flow is aborted when password confirmation
    does not match the provided password.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(PasswordMismatchError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password='Password@123',
            new_password_confirmation='Password@456',
        )

    # assert was not called
    mocks.hasher.hash.assert_not_called()
    mocks.token_manager.validate.assert_not_called()
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_password_hashing_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while hashing the new password.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.hasher.hash.side_effect = InfrastructureError(
        'Error attempting to hash password',
        InfrastructureErrorCode.PASSWORD_HASHER,
        Exception(),
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once_with(new_password)

    # assert was not called
    mocks.token_manager.validate.assert_not_called()
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_token_is_invalid(
    active_user: User,
):
    """
    The password change flow is aborted when the provided token
    is invalid.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.INVALID
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(InvalidTokenError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once_with(new_password)
    mocks.token_manager.validate.assert_called_once_with(token)

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_token_validation_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while validating the token.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error attempting to validate token',
        InfrastructureErrorCode.AUTH_TOKEN,
        Exception(),
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_token_type_is_invalid(
    active_user: User,
):
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    mocks.token_manager.validate.return_value = PayloadTokenDTO(
        jti='jti',
        sub=uuid.uuid4(),
        exp=int(exp.timestamp()),
        typ='refresh',  # incorrect type
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(InvalidTokenTypeError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.uow.token_repo.exists.assert_not_awaited()
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_token_existence_check_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while checking if the token exists.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.uow.token_repo.exists.side_effect = InfrastructureError(
        'Error attempting to check token existence',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_token_revocation_check_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while checking if the token is revoked.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.uow.token_repo.is_revoked.side_effect = InfrastructureError(
        'Error attempting to check token revocation',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once_with(new_password)
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_token_does_not_exist(
    active_user: User,
):
    """
    The password change flow is aborted when the token does not
    exist in persistence storage.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.uow.token_repo.exists.return_value = False

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(TokenNotFoundError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.is_revoked.assert_not_awaited()
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_token_is_revoked(
    active_user: User,
):
    """
    The password change flow is aborted when the token is revoked.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.uow.token_repo.is_revoked.return_value = True

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(TokenRevokedError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once_with(new_password)
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)

    # assert was not called
    mocks.uow.user_repo.get_by_public_id.assert_not_awaited()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_get_user_fails(
    active_user: User,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to fetch the user from the repository.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.uow.user_repo.get_by_public_id.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once_with(new_password)
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )

    # assert was not called
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_user_state_is_corrupted(
    active_user: User,
):
    """
    The returned user instance may raise a domain error when built in
    the repository layer. Test if this error propagates to the use
    case, aborting the password change flow.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=active_user,
        verification_code=None,
    )

    mocks.uow.user_repo.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once_with(new_password)
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once_with(
        active_user.public_id
    )

    # assert was not called
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_password_change_not_performed_when_user_does_not_exist():
    """
    The password change flow is aborted when the user does not exist.
    """
    mocks: DependenciesMocked = mocks_factory(
        user=None,
        verification_code=None,
    )

    use_case = ChangePasswordUseCase(
        token_manager=mocks.token_manager,
        uow=mocks.uow,
        hasher=mocks.hasher,
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            access=token,
            code='123456',
            new_password=new_password,
            new_password_confirmation=new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once_with(new_password)
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.uow.token_repo.exists.assert_awaited_once_with(jti)
    mocks.uow.token_repo.is_revoked.assert_awaited_once_with(jti)
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_user_is_inactive(
    inactive_user: User,
):
    """
    The password change flow is aborted if the authenticated user
    is inactive.
    """
    mocks: DependenciesMocked = mocks_factory(
        inactive_user,
        None,
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute(
            token,
            '123456',
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()

    # assert was not called
    mocks.uow.code_repo.get_by_user_id_and_code.assert_not_awaited()
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_get_code_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to fetch a verification code from the repository.
    """
    unused_code = create_unused_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.code_repo.get_by_user_id_and_code.side_effect = (
        InfrastructureError(
            'Error attempting to get verification code',
            InfrastructureErrorCode.DATABASE,
            Exception(),
        )
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token,
            unused_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_code_state_is_corrupted(
    active_user: User,
    create_unused_code,
):
    """
    The password change flow is aborted when the verification code
    returned by the repository cannot be reconstructed into a valid
    domain entity.
    """
    unused_code = create_unused_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.code_repo.get_by_user_id_and_code.side_effect = (
        CorruptedPersistenceStateError(DomainError('some domain error'))
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(
            token,
            unused_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_code_not_found(
    active_user: User,
):
    """
    The password change flow is aborted when the verification code
    does not exist for the authenticated user.
    """
    mocks: DependenciesMocked = mocks_factory(
        active_user,
        None,
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(VerificationCodeNotFoundError):
        await use_case.execute(
            token,
            '123456',
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_code_already_used(
    active_user: User,
    create_used_code,
):
    """
    The password change flow is aborted when the verification code
    has already been used.
    """
    used_code = create_used_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        used_code,
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(VerificationCodeAlreadyUsedError):
        await use_case.execute(
            token,
            used_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_code_type_is_invalid(
    active_user: User,
    create_unused_code,
):
    """
    The password change flow is aborted when the verification code
    type does not match the expected password change type.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(VerificationCodeTypeError):
        await use_case.execute(
            token,
            unused_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_code_is_expired(
    active_user: User,
    create_expired_code,
):
    """
    The password change flow is aborted when the verification code
    has expired.
    """
    expired_code = create_expired_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        expired_code,
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(VerificationCodeExpiredError):
        await use_case.execute(
            token,
            expired_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_awaited()
    mocks.uow.__aexit__.assert_not_awaited()
    mocks.uow.user_repo.update.assert_not_awaited()
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_update_user_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist the updated user password.
    """
    unused_code = create_unused_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.user_repo.update.side_effect = InfrastructureError(
        'Error attempting to update user password',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token,
            unused_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.user_repo.update.assert_awaited_once()

    # assert was not called
    mocks.uow.code_repo.update.assert_not_awaited()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_update_code_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to persist the used verification code state.
    """
    unused_code = create_unused_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.code_repo.update.side_effect = InfrastructureError(
        'Error attempting to update verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token,
            unused_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.code_repo.update.assert_awaited_once()

    # assert was not called
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_awaited()
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_revoke_tokens_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when an unexpected error occurs
    while trying to revoke all refresh tokens from the user.
    """
    unused_code = create_unused_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.token_repo.revoke_all_refreshes.side_effect = (
        InfrastructureError(
            'Error attempting to revoke refresh tokens',
            InfrastructureErrorCode.DATABASE,
            Exception(),
        )
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token,
            unused_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.code_repo.update.assert_awaited_once()
    mocks.uow.token_repo.revoke_all_refreshes.assert_awaited_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_awaited()


async def test_change_password_not_performed_when_create_message_fails(
    active_user: User,
    create_unused_code,
):
    """
    Test if an exception is raised when message persistence fails
    during password change finalization.
    """
    unused_code = create_unused_code(CodeType.CHANGE_PASSWORD)

    mocks: DependenciesMocked = mocks_factory(
        active_user,
        unused_code,
    )

    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to create message',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = ChangePasswordUseCase(
        mocks.token_manager,
        mocks.uow,
        mocks.hasher,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token,
            unused_code.code.value,
            new_password,
            new_password,
        )

    # assert was called
    mocks.hasher.hash.assert_called_once()
    mocks.token_manager.validate.assert_called_once()
    mocks.uow.token_repo.exists.assert_awaited_once()
    mocks.uow.token_repo.is_revoked.assert_awaited_once()
    mocks.uow.user_repo.get_by_public_id.assert_awaited_once()
    mocks.uow.code_repo.get_by_user_id_and_code.assert_awaited_once()
    mocks.uow.__aenter__.assert_awaited_once()
    mocks.uow.__aexit__.assert_awaited_once()
    mocks.uow.user_repo.update.assert_awaited_once()
    mocks.uow.code_repo.update.assert_awaited_once()
    mocks.uow.token_repo.revoke_all_refreshes.assert_awaited_once()
    mocks.uow.message_repo.create.assert_awaited_once()


@dataclass(frozen=True)
class DependenciesMocked:
    """
    Data structure containing the mocked dependencies for the
    password change use case.
    """

    token_manager: AsyncMock
    uow: AsyncMock
    hasher: AsyncMock


def mocks_factory(
    user: User | None,
    verification_code: VerificationCode | None,
) -> DependenciesMocked:
    """
    Create mocked dependencies for the password change use case.

    The configured mocks simulate token validation, repository
    lookups, password hashing, and transactional persistence
    operations used during the password change flow.
    """

    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_manager = AsyncMock(spec=TokenManagerPort)
    token_manager.validate.return_value = PayloadTokenDTO(
        sub=cast(uuid.UUID, user.public_id if user else None),
        jti=jti,
        exp=int(exp.timestamp()),
        typ='access',
    )

    hasher = AsyncMock(spec=HasherPort)
    hasher.hash.return_value = hashed_password

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.user_repo.get_by_public_id.return_value = user
    uow.user_repo.update.return_value = None

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.update.return_value = None
    uow.code_repo.get_by_user_id_and_code.return_value = verification_code

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    uow.token_repo = AsyncMock(spec=TokenRepositoryPort)
    uow.token_repo.revoke_all_refreshes.return_value = None
    uow.token_repo.exists.return_value = True
    uow.token_repo.is_revoked.return_value = False

    return DependenciesMocked(
        token_manager=token_manager,
        uow=uow,
        hasher=hasher,
    )
