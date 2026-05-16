import uuid
from datetime import datetime, timedelta, timezone

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
from unit.application.use_cases.user.types import EmailVerificationDependencies

public_id = uuid.uuid4()
email = 'email@email.com'
created_at = datetime.now(timezone.utc)
updated_at = created_at
hash_password = 'password_hashed'
email_not_verified = False
email_verified = True
is_active = True
is_inactive = False
last_login_at = None
code = '123456'
correct_code_type = CodeType.EMAIL_VERIFICATION.value
incorrect_code_type = CodeType.CHANGE_PASSWORD.value
code_not_expired = created_at + timedelta(minutes=15)
code_expired = datetime.now(timezone.utc) + +timedelta(milliseconds=1)
code_not_used = None
code_used = datetime.now(timezone.utc)
code_not_sent = None
without_payload = None
login_link = 'www.auth.com/login'


async def test_email_verified_successfully(
    email_verification_dependencies, unverified_user: User
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

    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user,
        code_persistence,
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    await use_case.execute(unverified_user.email.value, code, login_link)

    deps.user_repo.get_by_email.assert_called_once_with(
        unverified_user.email.value
    )
    deps.code_repo.get_by_user_id_and_code.assert_called_once_with(
        unverified_user.public_id, code
    )
    deps.uow.__aenter__.assert_called_once()
    deps.uow.__aexit__.assert_called_once()

    deps.uow.user_repo.update.assert_called_once()
    user: User = deps.uow.user_repo.update.call_args[0][0]
    assert user.public_id == unverified_user.public_id
    assert user.email.value == unverified_user.email.value
    assert user.hash_password.value == unverified_user.hash_password.value
    assert user.created_at == unverified_user.created_at
    assert user.email_verified is True
    assert user.is_active is True
    assert user.last_login_at == unverified_user.last_login_at
    assert user.updated_at > unverified_user.created_at

    deps.uow.code_repo.update.assert_called_once()
    code_args: VerificationCodePersistenceDTO = (
        deps.uow.code_repo.update.call_args[0][0]
    )
    assert code_args.code == code_persistence.code
    assert code_args.user_public_id == code_persistence.user_public_id
    assert code_args.payload is None
    assert code_args.created_at == code_persistence.created_at
    assert code_args.expires_at == code_persistence.expires_at
    assert isinstance(code_args.used_at, datetime)
    assert code_args.sent_at is None
    assert code_args.type == CodeType.EMAIL_VERIFICATION.value

    deps.uow.message_repo.create.assert_called_once()
    message: Message = deps.uow.message_repo.create.call_args[0][0]
    assert message.id is not None
    assert message.type == MessageType.SEND_NOTIFICATION_EMAIL_VERIFIED
    payload = message.payload.to_dict()
    assert payload['to'] == user.email.value
    assert payload['link'] == login_link
    assert payload['subject'] == 'Email verified successfully'


async def test_verification_fails_when_user_does_not_exist(
    email_verification_dependencies,
):
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    deps: EmailVerificationDependencies = email_verification_dependencies(
        None,
        code_persistence,
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    with pytest.raises(UserNotFoundError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()

    deps.code_repo.get_by_user_id_and_code.assert_not_called()
    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_user_already_verified(
    email_verification_dependencies, verified_user: User
):
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

    deps: EmailVerificationDependencies = email_verification_dependencies(
        verified_user,
        code_persistence,
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    with pytest.raises(EmailAlreadyVerifiedError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()

    deps.code_repo.get_by_user_id_and_code.assert_not_called()
    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_user_inactive(
    email_verification_dependencies, inactive_user: User
):

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

    deps: EmailVerificationDependencies = email_verification_dependencies(
        inactive_user,
        code_persistence,
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    with pytest.raises(InactiveUserError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()

    deps.code_repo.get_by_user_id_and_code.assert_not_called()
    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_get_user_fails(
    email_verification_dependencies,
):
    deps: EmailVerificationDependencies = email_verification_dependencies(
        None,
        None,
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    deps.user_repo.get_by_email.side_effect = InfrastructureError(
        'Error attempting to get user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()

    deps.code_repo.get_by_user_id_and_code.assert_not_called()
    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_does_not_exist(
    email_verification_dependencies, unverified_user: User
):

    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user, None
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    with pytest.raises(VerificationCodeNotFoundError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()
    deps.code_repo.get_by_user_id_and_code.assert_called_once()

    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_already_used(
    email_verification_dependencies, unverified_user: User
):
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_used,  # set code as used
        sent_at=code_not_sent,
        payload=without_payload,
    )

    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user, code_persistence
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    with pytest.raises(VerificationCodeAlreadyUsedError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()
    deps.code_repo.get_by_user_id_and_code.assert_called_once()

    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_expired(
    email_verification_dependencies, unverified_user: User
):
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_expired,  # set code as expired
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user, code_persistence
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    with pytest.raises(VerificationCodeExpiredError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()
    deps.code_repo.get_by_user_id_and_code.assert_called_once()

    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_code_type_is_invalid(
    email_verification_dependencies, unverified_user: User
):
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=public_id,
        type=incorrect_code_type,  # set code as incorrect tye
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user, code_persistence
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    with pytest.raises(VerificationCodeTypeError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()
    deps.code_repo.get_by_user_id_and_code.assert_called_once()

    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()
    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_get_code_fails(
    email_verification_dependencies, unverified_user: User
):
    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user,
        None,
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    deps.code_repo.get_by_user_id_and_code.side_effect = InfrastructureError(
        'Error attempting to get code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()
    deps.code_repo.get_by_user_id_and_code.assert_called_once()

    deps.uow.user_repo.update.assert_not_called()
    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()


async def test_verification_fails_when_persist_user_update_fails(
    email_verification_dependencies, unverified_user: User
):
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user, code_persistence
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    deps.uow.user_repo.update.side_effect = InfrastructureError(
        'Error attempting to update user',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()
    deps.code_repo.get_by_user_id_and_code.assert_called_once()
    deps.uow.user_repo.update.assert_called_once()
    deps.uow.__aexit__.assert_called_once()
    deps.uow.__aenter__.assert_called_once()

    deps.uow.code_repo.update.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_persist_code_update_fails(
    email_verification_dependencies, unverified_user: User
):
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user, code_persistence
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    deps.uow.code_repo.update.side_effect = InfrastructureError(
        'Error attempting to update code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()
    deps.code_repo.get_by_user_id_and_code.assert_called_once()
    deps.uow.user_repo.update.assert_called_once()
    deps.uow.code_repo.update.assert_called_once()
    deps.uow.__aexit__.assert_called_once()
    deps.uow.__aenter__.assert_called_once()

    deps.uow.message_repo.create.assert_not_called()


async def test_verification_fails_when_message_persists_fails(
    email_verification_dependencies, unverified_user: User
):
    code_persistence = VerificationCodePersistenceDTO(
        code=code,
        user_public_id=public_id,
        type=correct_code_type,
        created_at=created_at,
        expires_at=code_not_expired,
        used_at=code_not_used,
        sent_at=code_not_sent,
        payload=without_payload,
    )

    deps: EmailVerificationDependencies = email_verification_dependencies(
        unverified_user, code_persistence
    )

    use_case = EmailVerificationUseCase(
        deps.user_repo, deps.code_repo, deps.uow
    )

    deps.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist message',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    with pytest.raises(InfrastructureError):
        await use_case.execute(email, code, login_link)

    deps.user_repo.get_by_email.assert_called_once()
    deps.code_repo.get_by_user_id_and_code.assert_called_once()
    deps.uow.user_repo.update.assert_called_once()
    deps.uow.code_repo.update.assert_called_once()
    deps.uow.message_repo.create.assert_called_once()
    deps.uow.__aexit__.assert_called_once()
    deps.uow.__aenter__.assert_called_once()
