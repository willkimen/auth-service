import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from application.dtos.verification_code_dto import (
    VerificationCodePersistenceDTO,
)
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
    UserNotFoundError,
    VerificationCodeNotFoundError,
)
from application.messages.message import Message
from application.messages.message_types import MessageType
from application.ports.output import (
    MessageRepositoryPort,
    UnitOfWorkPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)
from application.use_cases.user.email_verification import (
    EmailVerificationUseCase,
)
from domain.entities.user import User
from domain.enums import CodeType
from domain.exceptions import (
    EmailAlreadyVerifiedError,
    InactiveUserError,
    VerificationCodeAlreadyUsedError,
    VerificationCodeExpiredError,
    VerificationCodeTypeError,
)

# verification code state
code = '123456'
created_at = datetime.now(timezone.utc)

correct_code_type = CodeType.EMAIL_VERIFICATION.value
incorrect_code_type = CodeType.CHANGE_PASSWORD.value
code_not_expired = created_at + timedelta(minutes=15)
code_expired = datetime.now(timezone.utc) + +timedelta(milliseconds=1)
code_not_used = None
code_used = datetime.now(timezone.utc)
code_not_sent = None
without_payload = None

# args para use_case.execute()
login_link = 'www.auth.com/login'
subject = 'Email verified successfully'


async def test_email_verified_successfully(unverified_user: User):
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=unverified_user.public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(unverified_user, code_persistence)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act
    await use_case.execute(
        unverified_user.email.value, code_persistence.code, login_link
    )

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once_with(
        unverified_user.email.value
    )
    mocks.code_repo.get_by_user_id_and_code.assert_called_once_with(
        unverified_user.public_id, code_persistence.code
    )
    mocks.uow.__aenter__.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.message_repo.create.assert_called_once()

    # assert that user_repo.update() was called with correct arguments
    user_arg: User = mocks.uow.user_repo.update.call_args[0][0]
    assert user_arg.public_id == unverified_user.public_id
    assert user_arg.email.value == unverified_user.email.value
    assert user_arg.hash_password.value == unverified_user.hash_password.value
    assert user_arg.created_at == unverified_user.created_at
    assert user_arg.email_verified is True
    assert user_arg.is_active is True
    assert user_arg.last_login_at == unverified_user.last_login_at
    assert user_arg.updated_at == unverified_user.updated_at

    # assert that code_repo.update() was called with correct arguments
    code_arg: VerificationCodePersistenceDTO = (
        mocks.uow.code_repo.update.call_args[0][0]
    )
    assert code_arg.code == code_persistence.code
    assert code_arg.user_public_id == code_persistence.user_public_id
    assert code_arg.payload is None
    assert code_arg.created_at == code_persistence.created_at
    assert code_arg.expires_at == code_persistence.expires_at
    assert isinstance(code_arg.used_at, datetime)
    assert code_arg.sent_at is None
    assert code_arg.type == CodeType.EMAIL_VERIFICATION.value

    # assert that message.create() was called with correct arguments
    message_arg: Message = mocks.uow.message_repo.create.call_args[0][0]
    assert message_arg.id is not None
    assert message_arg.type == MessageType.SEND_NOTIFICATION_EMAIL_VERIFIED
    payload = message_arg.payload.to_dict()
    assert payload['to'] == user_arg.email.value
    assert payload['link'] == login_link
    assert payload['subject'] == subject


async def test_verification_fails_when_user_does_not_exist():
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=uuid.uuid4(),
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(None, code_persistence)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_user_already_verified(
    verified_user: User,
):
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=verified_user.public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(verified_user, code_persistence)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(EmailAlreadyVerifiedError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_user_inactive(inactive_user: User):
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=inactive_user.public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(inactive_user, code_persistence)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_get_user_fails():
    # arrange
    mocks = mocks_factory(None, None)

    mocks.user_repo.get_by_email.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()

    # assert was not called
    mocks.code_repo.get_by_user_id_and_code.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_does_not_exist(
    unverified_user: User,
):
    # arrange
    mocks = mocks_factory(unverified_user, None)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and arrange
    with pytest.raises(VerificationCodeNotFoundError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_already_used(
    unverified_user: User,
):
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=unverified_user.public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_used,  # set code as used
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(unverified_user, code_persistence)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(VerificationCodeAlreadyUsedError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_expired(unverified_user: User):
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=unverified_user.public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_expired,  # set code as expired
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(unverified_user, code_persistence)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(VerificationCodeExpiredError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_type_is_invalid(
    unverified_user: User,
):
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=unverified_user.public_id,
        type=incorrect_code_type,  # set code as incorrect tye
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(unverified_user, code_persistence)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(VerificationCodeTypeError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_get_code_fails(unverified_user: User):
    # arrange
    mocks = mocks_factory(unverified_user, None)

    mocks.code_repo.get_by_user_id_and_code.side_effect = InfrastructureError(
        'Error attempting to get code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act anda assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()

    # assert was not called
    mocks.uow.user_repo.update.assert_not_called()
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()
    mocks.uow.__aenter__.assert_not_called()
    mocks.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_persist_user_update_fails(
    unverified_user: User,
):
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=unverified_user.public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(unverified_user, code_persistence)

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    mocks.uow.user_repo.update.side_effect = InfrastructureError(
        'Error attempting to update user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()

    # assert was not called
    mocks.uow.code_repo.update.assert_not_called()
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_persist_code_update_fails(
    unverified_user: User,
):
    # arrange
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=unverified_user.public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(unverified_user, code_persistence)

    mocks.uow.code_repo.update.side_effect = InfrastructureError(
        'Error attempting to update code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', '')

    # assert was called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()

    # assert was not called
    mocks.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_message_persists_fails(
    unverified_user: User,
):
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=unverified_user.public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    mocks = mocks_factory(unverified_user, code_persistence)

    mocks.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist message',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = EmailVerificationUseCase(
        mocks.user_repo, mocks.code_repo, mocks.uow
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute('', '', '')

    # assert was not called
    mocks.user_repo.get_by_email.assert_called_once()
    mocks.code_repo.get_by_user_id_and_code.assert_called_once()
    mocks.uow.user_repo.update.assert_called_once()
    mocks.uow.code_repo.update.assert_called_once()
    mocks.uow.message_repo.create.assert_called_once()
    mocks.uow.__aexit__.assert_called_once()
    mocks.uow.__aenter__.assert_called_once()


@dataclass(frozen=True)
class DependeciesMocked:
    user_repo: AsyncMock
    code_repo: AsyncMock
    uow: AsyncMock


def mocks_factory(
    user: User | None,
    code_persistence_dto: VerificationCodePersistenceDTO | None,
) -> DependeciesMocked:
    user_repo = AsyncMock(spec=UserRepositoryPort)
    user_repo.get_by_email.return_value = user

    code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    code_repo.get_by_user_id_and_code.return_value = code_persistence_dto

    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.__aenter__.return_value = uow
    uow.__aexit__.return_value = False

    uow.user_repo = AsyncMock(spec=UserRepositoryPort)
    uow.user_repo.update.return_value = None

    uow.code_repo = AsyncMock(spec=VerificationCodeRepositoryPort)
    uow.code_repo.update.return_value = None

    uow.message_repo = AsyncMock(spec=MessageRepositoryPort)
    uow.message_repo.create.return_value = None

    return DependeciesMocked(user_repo, code_repo, uow)
