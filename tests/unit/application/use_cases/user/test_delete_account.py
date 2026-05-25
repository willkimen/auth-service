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
    TokenError,
    TokenErrorCode,
    TokenNotFoundError,
    TokenRevokedError,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.email_payloads import AccountDeletedPayload
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
from application.use_cases.user.delete_account import DeleteUseCase
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.exceptions import (
    DomainError,
    InactiveUserError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)

jti = 'jti'
token = 'token'


@pytest.mark.asyncio
async def test_delete_account_successfully(
    active_user: User, create_unused_code
):
    """
    Test if the delete account use case executes successfully.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    # act
    await use_case.execute(token, unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once_with(token)
    mocks.token_repo.exists.assert_called_once_with(jti)
    mocks.token_repo.is_revoke.assert_called_once_with(jti)
    mocks.user_repo.get_by_public_id.assert_called_once_with(
        active_user.public_id
    )
    mocks.code_repo.get_by_user_id_and_code.assert_called_once_with(
        active_user.public_id,
        unused_code.code.value,
    )
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.user_repo.delete.assert_called_once_with(active_user.public_id)
    mocks.uow.code_repo.delete_all.assert_called_once_with(
        active_user.public_id
    )
    mocks.uow.token_repo.revoke_all_refreshes.assert_called_once_with(
        active_user.public_id
    )
    mocks.uow.message_repo.create.assert_called_once()

    # assert message.create() arguments
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.type == MessageType.NOTIFICATION_DELETED

    payload: AccountDeletedPayload = message_arg.payload
    assert payload.to == active_user.email.value


async def test_delete_not_performed_when_token_is_invalid(
    active_user: User,
    create_unused_code,
):
    """
    The delete account flow is aborted when token validation fails
    with a domain-level TokenError.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.token_manager.validate.side_effect = TokenError(
        TokenErrorCode.INVALID
    )
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    # act and assert
    with pytest.raises(TokenError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.exists.assert_not_called()
    mocks.token_repo.is_revoke.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_token_validation_fails(
    active_user: User,
    create_unused_code,
):
    """
    The delete account flow is aborted when token validation
    fails due to an infrastructure error.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.token_manager.validate.side_effect = InfrastructureError(
        'Error validating token',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()

    # assert was not called
    mocks.token_repo.exists.assert_not_called()
    mocks.token_repo.is_revoke.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_token_exists_check_fails(
    active_user: User,
    create_unused_code,
):
    """
    The delete account flow is aborted when token existence check
    fails due to an infrastructure error.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.token_repo.exists.side_effect = InfrastructureError(
        'Error checking token existence',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()

    # assert was not called
    mocks.token_repo.is_revoke.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_token_not_found(
    active_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.token_repo.exists.return_value = False
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(TokenNotFoundError):
        await use_case.execute(token=token, code=unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()

    # assert was not called
    mocks.token_repo.is_revoke.assert_not_called()
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_token_revoke_check_fails(
    active_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.token_repo.is_revoke.side_effect = InfrastructureError(
        'Error checking token revocation',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()

    # assert was not called
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_token_is_revoked(
    active_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.token_repo.is_revoke.return_value = True
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(TokenRevokedError):
        await use_case.execute(token=token, code=unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()

    # assert was not called
    mocks.user_repo.get_by_public_id.assert_not_called()
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_get_user_fails(
    active_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.user_repo.get_by_public_id.side_effect = InfrastructureError(
        'Error fetching user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(token=token, code=unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_user_state_is_corrupted(
    active_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.user_repo.get_by_public_id.side_effect = (
        CorruptedPersistenceStateError(DomainError('corrupted'))
    )
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(token=token, code=unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_user_not_found(
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(None, unused_code)
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(UserNotFoundError):
        await use_case.execute(token=token, code=unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_user_is_inactive(
    inactive_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(inactive_user, unused_code)
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InactiveUserError):
        await use_case.execute(token=token, code=unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_get_code_fails(
    active_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.code_repo.get_by_user_id_and_code.side_effect = InfrastructureError(
        'Error fetching code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(token=token, code=unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_code_state_is_corrupted(
    active_user: User,
    create_unused_code,
):
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.code_repo.get_by_user_id_and_code.side_effect = (
        CorruptedPersistenceStateError(DomainError('corrupted'))
    )
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(CorruptedPersistenceStateError):
        await use_case.execute(token=token, code=unused_code.code.value)

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_code_not_found(
    active_user: User,
):
    """
    The delete account flow is aborted when code does not exist.
    """
    mocks = mocks_factory(active_user, None)
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(VerificationCodeNotFoundError):
        await use_case.execute(
            token=token,
            code='123456',
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_code_already_used(
    active_user: User,
    create_used_code,
):
    """
    The delete account flow is aborted when code is already used.
    """
    used_code = create_used_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, used_code)
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(VerificationCodeAlreadyUsedError):
        await use_case.execute(
            token=token,
            code=used_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_code_type_is_invalid(
    active_user: User,
    create_unused_code,
):
    """
    The delete account flow is aborted when verification code type
    is not DELETE_ACCOUNT.
    """
    unused_code = create_unused_code(CodeType.EMAIL_VERIFICATION)
    mocks = mocks_factory(active_user, unused_code)
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(VerificationCodeTypeError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_code_is_expired(
    active_user: User,
    create_expired_code,
):
    """
    The delete account flow is aborted when verification code is expired.
    """
    expired_code = create_expired_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, expired_code)
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(VerificationCodeExpiredError):
        await use_case.execute(
            token=token,
            code=expired_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.delete.assert_not_called()
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_user_delete_fails(
    active_user: User,
    create_unused_code,
):
    """
    The delete account flow is aborted when user deletion fails.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.uow.user_repo.delete.side_effect = InfrastructureError(
        'Error deleting user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.user_repo.delete.assert_called_once()

    # assert was not called
    mocks.uow.code_repo.delete_all.assert_not_called()
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_code_delete_all_fails(
    active_user: User,
    create_unused_code,
):
    """
    The delete account flow is aborted when code deletion fails.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)

    mocks.uow.code_repo.delete_all.side_effect = InfrastructureError(
        'Error deleting codes',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # asert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.user_repo.delete.assert_called_once()
    mocks.uow.code_repo.delete_all.assert_called_once()

    # assert was not calledd
    mocks.uow.token_repo.revoke_all_refreshes.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_revoke_tokens_fails(
    active_user: User,
    create_unused_code,
):
    """
    The delete account flow is aborted when token revocation fails.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.uow.token_repo.revoke_all_refreshes.side_effect = (
        InfrastructureError(
            'Error revoking refresh tokens',
            InfrastructureErrorCode.DATABASE,
            Exception(),
        )
    )
    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.user_repo.delete.assert_called_once()
    mocks.uow.code_repo.delete_all.assert_called_once()
    mocks.uow.token_repo.revoke_all_refreshes.assert_called_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_called()


async def test_delete_not_performed_when_message_create_fails(
    active_user: User,
    create_unused_code,
):
    """
    The delete account flow is aborted when message creation fails.
    """
    unused_code = create_unused_code(CodeType.DELETE_ACCOUNT)
    mocks = mocks_factory(active_user, unused_code)
    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error creating message',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = DeleteUseCase(
        user_repo=mocks.user_repo,
        code_repo=mocks.code_repo,
        token_repo=mocks.token_repo,
        token_manager=mocks.token_manager,
        uow=mocks.uow,
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(
            token=token,
            code=unused_code.code.value,
        )

    # assert was called
    mocks.token_manager.validate.assert_called_once()
    mocks.token_repo.exists.assert_called_once()
    mocks.token_repo.is_revoke.assert_called_once()
    mocks.user_repo.get_by_public_id.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.user_repo.delete.assert_called_once()
    mocks.uow.code_repo.delete_all.assert_called_once()
    mocks.uow.token_repo.revoke_all_refreshes.assert_called_once()
    mocks.uow.message_repo.create.assert_called_once()


@dataclass(frozen=True)
class DependenciesMocked:
    user_repo: AsyncMock
    code_repo: AsyncMock
    token_repo: AsyncMock
    token_manager: Mock
    uow: AsyncMock


def mocks_factory(
    user: User | None, verification_code: VerificationCode | None
) -> DependenciesMocked:
    user_repo = AsyncMock(spec=UserRepositoryPort)
    user_repo.get_by_public_id.return_value = user

    code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    code_repo.get_by_user_id_and_code.return_value = verification_code

    token_repo = AsyncMock(spec=TokenRepositoryPort)
    token_repo.exists.return_value = True
    token_repo.is_revoke.return_value = False

    token_manager = Mock(spec=TokenManagerPort)
    token_manager.validate.return_value = PayloadTokenDTO(
        jti=jti,
        sub=cast(uuid.UUID, user.public_id if user else None),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.token_repo = AsyncMock(spec=TokenRepositoryPort)
    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)

    uow.user_repo.delete.return_value = None
    uow.code_repo.delete_all.return_value = None
    uow.token_repo.revoke_all_refreshes.return_value = None
    uow.message_repo.create.return_value = None

    return DependenciesMocked(
        user_repo=user_repo,
        code_repo=code_repo,
        token_repo=token_repo,
        token_manager=token_manager,
        uow=uow,
    )
