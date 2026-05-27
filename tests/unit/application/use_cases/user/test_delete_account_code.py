import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest

from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    CorruptedPersistenceStateError,
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidTokenError,
    InvalidTokenErrorCode,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
)
from application.messages.email_payloads import DeleteAccountPayload
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    MessageRepositoryPort,
    TokenManagerPort,
    TokenRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.delete_account_code import DeleteCodeUseCase
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import DomainError, InactiveUserError
from domain.value_objects.code import Code

access = 'access'
jti = 'jti'
code_expiration_time = 15


async def test_initialize_account_deletion_process_successfully(
    active_user: User,
):
    """
    Test if the complete flow initializing account deletion
    authorization runs successfully.

    Success is verified by checking if all required operations
    are executed with the correct expected arguments.

    Args:
        active_user (User):
            An active user instance used during the account
            deletion flow.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act
    await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)
    mocks.user_repo.get_by_public_id.assert_called_once_with(
        active_user.public_id
    )
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.code_repo.create.assert_called_once()
    mocks.uow.message_repo.create.assert_called_once()

    # assert that code_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a VerificationCode instance,
    # which must contain the following state:
    code_arg: VerificationCode = mocks.uow.code_repo.create.call_args[0][0]
    assert code_arg.user_public_id == active_user.public_id
    assert code_arg.used_at is None
    assert code_arg.payload is None
    assert code_arg.expires_at > code_arg.created_at
    assert code_arg.type == CodeType.DELETE_ACCOUNT
    assert code_arg.is_active(datetime.now(timezone.utc))

    code: Code = code_arg.code
    assert isinstance(code.value, str)
    number_digits = 6
    assert len(code.value) == number_digits
    assert code.value.isdigit()

    # assert that message_repo.create()
    # was called with the correct expected arguments.
    # The expected argument is a Message instance,
    # which must contain the following state:
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.type == MessageType.DELETE_CODE

    payload: DeleteAccountPayload = message_arg.payload
    assert payload.to == active_user.email.value
    assert payload.code == code_arg.code.value
    assert payload.expiration == str(code_expiration_time)
    assert payload.subject == 'Confirm account deletion'


async def test_delete_not_initialize_process_when_token_validation_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while validating the token.

    The account deletion flow must be aborted before any persistence
    or user lookup operations occur.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error validating token',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)

    # assert was not called
    mocks.token_repo.exists.assert_not_called()
    mocks.token_repo.is_revoke.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_token_is_invalid(
    active_user: User,
):
    """
    Test if the account deletion flow is aborted when the token
    validation fails with a InvalidTokenError.

    No persistence or user lookup operations should be executed.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    mocks.token_manager.validate.side_effect = InvalidTokenError(
        InvalidTokenErrorCode.INVALID
    )

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InvalidTokenError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)

    # assert was not called
    mocks.token_repo.exists.assert_not_called()
    mocks.token_repo.is_revoke.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_token_check_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while checking token existence in persistence.

    The flow must be aborted before revoked-token validation,
    user retrieval, or any transactional operations.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    mocks.token_repo.exists.side_effect = InfrastructureError(
        'Error checking token existence',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)

    # assert was not called
    mocks.token_repo.is_revoke.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_token_not_found(
    active_user: User,
):
    """
    Test if the account deletion flow is aborted when the token
    does not exist in persistence.

    No further validation or persistence operations should occur.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)
    mocks.token_repo.exists.return_value = False

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenNotFoundError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)

    # assert was not called
    mocks.token_repo.is_revoke.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_token_revoke_check_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while checking if the token is revoked.

    The flow must be aborted before user retrieval and persistence.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    mocks.token_repo.is_revoke.side_effect = InfrastructureError(
        'Error checking token revocation',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)

    # assert was not called
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_token_is_revoked(
    active_user: User,
):
    """
    Test if the account deletion flow is aborted when the token
    is marked as revoked.

    No user lookup or persistence operations should occur.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)
    mocks.token_repo.is_revoke.return_value = True

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenRevokedError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)

    # assert was not called
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_get_user_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while retrieving the user from persistence.

    The flow must stop before any domain validation or transactional logic.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    mocks.user_repo.get_by_public_id.side_effect = InfrastructureError(
        'Error fetching user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)
    mocks.user_repo.get_by_public_id.assert_called_once_with(
        active_user.public_id
    )

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_user_state_is_corrupted(
    active_user: User,
):
    """
    Test if a corrupted persistence state error is propagated when
    the repository returns invalid or unreconstructable user data.

    The flow must be aborted before any domain validation or persistence.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    mocks.user_repo.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('corrupted state'))
    )

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)
    mocks.user_repo.get_by_public_id.assert_called_once_with(
        active_user.public_id
    )

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_user_not_found():
    """
    Test if the delete account code flow is aborted when the user
    does not exist in persistence.

    No transactional or persistence operations must be executed.
    """
    mocks: DependenciesMocked = mocks_factory(None)

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)
    mocks.user_repo.get_by_public_id.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_user_is_inactive(
    inactive_user: User,
):
    """
    Test if the delete account code flow is aborted when the user
    is inactive.

    No verification code generation or persistence should occur.
    """
    mocks: DependenciesMocked = mocks_factory(inactive_user)

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)
    mocks.user_repo.get_by_public_id.assert_called_once_with(
        inactive_user.public_id
    )

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.code_repo.create.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_persist_code_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while persisting the verification code.

    The transaction must be started, but message persistence must
    not be reached.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    mocks.uow.code_repo.create.side_effect = InfrastructureError(
        'Error persisting verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)
    mocks.user_repo.get_by_public_id.assert_called_once_with(
        active_user.public_id
    )
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.code_repo.create.assert_called_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_account_not_initialize_when_persist_message_fails(
    active_user: User,
):
    """
    Test if an infrastructure exception is propagated when the use
    case fails while persisting the message.

    The code must be created successfully, but message persistence
    must interrupt the flow.
    """
    mocks: DependenciesMocked = mocks_factory(active_user)

    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error persisting message',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteCodeUseCase(
        mocks.user_repo,
        mocks.token_repo,
        mocks.token_manager,
        mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(access, code_expiration_time)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(access)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)
    mocks.user_repo.get_by_public_id.assert_called_once_with(
        active_user.public_id
    )
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.code_repo.create.assert_called_once()
    mocks.uow.message_repo.create.assert_called_once()


@dataclass
class DependenciesMocked:
    user_repo: AsyncMock
    token_repo: AsyncMock
    token_manager: Mock
    uow: AsyncMock


def mocks_factory(user: User | None) -> DependenciesMocked:
    user_repo = AsyncMock(spec=UserRepositoryPort)
    user_repo.get_by_public_id.return_value = user

    token_repo = AsyncMock(spec=TokenRepositoryPort)
    token_repo.exists.return_value = True
    token_repo.is_revoke.return_value = False

    token_manager = Mock(spec=TokenManagerPort)
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    token_manager.validate.return_value = PayloadTokenDTO(
        sub=cast(uuid.UUID, user.public_id if user else None),
        jti=jti,
        exp=int(exp.timestamp()),
        typ='access',
    )

    uow = AsyncMock(spec=UnitOfWorkPort)

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.create.return_value = None

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = None

    return DependenciesMocked(
        user_repo=user_repo,
        token_repo=token_repo,
        token_manager=token_manager,
        uow=uow,
    )
