import uuid
from datetime import datetime, timezone

import pytest

from application.dtos.user_dto import UserPersistenceDTO
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
    UserNotFoundError,
)
from application.messages.message_types import MessageType
from application.use_cases.user.send_email_verification_code import (
    SendEmailVerificationCodeUseCase,
)
from domain.enums import CodeType
from domain.exceptions import EmailAlreadyVerifiedError, InactiveUserError
from unit.application.use_cases.user.types import (
    SendEmailVerificationCodeDependencies,
)


async def test_initialize_email_verification_process_successfully(
    send_email_verification_code_dependencies,
):
    # arrange
    public_id = uuid.uuid4()
    email = 'email@email.com'
    user_persistence = UserPersistenceDTO(
        public_id=public_id,
        email=email,
        hash_password='password-hashed',
        email_verified=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )

    deps: SendEmailVerificationCodeDependencies = (
        send_email_verification_code_dependencies(user_persistence)
    )

    use_case = SendEmailVerificationCodeUseCase(deps.user_repo, deps.uow)

    # act
    await use_case.execute(
        email='email@email.com',
        code_expiration_time=15,
        link='www.test.com/send-code',
        deadline=7,
    )

    # Assert that .get_by_email() was called with the
    # correct expected arguments.
    deps.user_repo.get_by_email.assert_called_once_with(email)
    deps.uow.__aenter__.assert_called()
    deps.uow.__aexit__.assert_called()

    # Assert that .create() was called with the correct expected arguments.
    deps.uow.code_repo.create.assert_called_once()
    saved_code_dto = deps.uow.code_repo.create.call_args[0][0]
    assert saved_code_dto.user_public_id == public_id
    assert saved_code_dto.used_at is None
    assert saved_code_dto.sent_at is None

    code_value = saved_code_dto.code
    assert isinstance(code_value, str)
    number_digits = 6
    assert len(code_value) == number_digits
    assert code_value.isdigit()

    assert saved_code_dto.expires_at > saved_code_dto.created_at
    assert saved_code_dto.payload is None

    assert saved_code_dto.type is CodeType.EMAIL_VERIFICATION.value

    # Assert that .create() was called with the correct expected arguments.
    deps.uow.message_repo.create.assert_called()
    message = deps.uow.message_repo.create.call_args[0][0]
    assert message.type == (MessageType.SEND_EMAIL_VERIFICATION_CODE.value)
    assert message.payload.to == 'email@email.com'
    assert message.payload.link == 'www.test.com/send-code'
    assert message.payload.expiration == '15'
    assert message.payload.deadline == '7'
    assert message.payload.code == saved_code_dto.code


async def test_verification_process_not_initialize_when_user_not_found(
    send_email_verification_code_dependencies,
):
    # arrange
    deps: SendEmailVerificationCodeDependencies = (
        send_email_verification_code_dependencies(None)
    )

    use_case = SendEmailVerificationCodeUseCase(deps.user_repo, deps.uow)

    # act and assert
    with pytest.raises(UserNotFoundError):
        await use_case.execute(
            email='email@email.com',
            code_expiration_time=15,
            link='www.test.com/send-code',
            deadline=7,
        )

    # assert
    deps.user_repo.get_by_email.assert_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()
    deps.uow.code_repo.create.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()


async def test_verification_process_not_initialize_when_user_already_verified(
    send_email_verification_code_dependencies,
):
    # arrange
    # Create an user already verified
    user_persistence = UserPersistenceDTO(
        public_id=uuid.uuid4(),
        email='email@email.com',
        hash_password='password-hashed',
        email_verified=True,  # already verified
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )

    deps: SendEmailVerificationCodeDependencies = (
        send_email_verification_code_dependencies(user_persistence)
    )

    use_case = SendEmailVerificationCodeUseCase(deps.user_repo, deps.uow)

    # act and assert
    with pytest.raises(EmailAlreadyVerifiedError):
        await use_case.execute(
            email='email@email.com',
            code_expiration_time=15,
            link='www.test.com/send-code',
            deadline=7,
        )

    # assert
    deps.user_repo.get_by_email.assert_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()
    deps.uow.code_repo.create.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()


async def test_verification_process_not_initialize_when_user_is_inactive(
    send_email_verification_code_dependencies,
):
    # arrange
    # Create an user is inactive
    user_persistence = UserPersistenceDTO(
        public_id=uuid.uuid4(),
        email='email@email.com',
        hash_password='password-hashed',
        email_verified=False,
        is_active=False,  # inactive
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )

    deps: SendEmailVerificationCodeDependencies = (
        send_email_verification_code_dependencies(user_persistence)
    )

    use_case = SendEmailVerificationCodeUseCase(deps.user_repo, deps.uow)

    # act and assert
    with pytest.raises(InactiveUserError):
        await use_case.execute(
            email='email@email.com',
            code_expiration_time=15,
            link='www.test.com/send-code',
            deadline=7,
        )

    # assert
    deps.user_repo.get_by_email.assert_called()
    deps.uow.__aenter__.assert_not_called()
    deps.uow.__aexit__.assert_not_called()
    deps.uow.code_repo.create.assert_not_called()
    deps.uow.message_repo.create.assert_not_called()


async def test_verification_process_not_initialize_when_persists_code_fails(
    send_email_verification_code_dependencies,
):
    # arrange
    user_persistence = UserPersistenceDTO(
        public_id=uuid.uuid4(),
        email='email@email.com',
        hash_password='password-hashed',
        email_verified=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )

    deps: SendEmailVerificationCodeDependencies = (
        send_email_verification_code_dependencies(user_persistence)
    )

    deps.uow.code_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = SendEmailVerificationCodeUseCase(deps.user_repo, deps.uow)

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email='email@email.com',
            code_expiration_time=15,
            link='www.test.com/send-code',
            deadline=7,
        )

    # assert
    deps.user_repo.get_by_email.assert_called()
    deps.uow.__aenter__.assert_called()
    deps.uow.__aexit__.assert_called()
    deps.uow.code_repo.create.assert_called()
    deps.uow.message_repo.create.assert_not_called()


async def test_verification_process_not_initialize_when_message_persits_fails(
    send_email_verification_code_dependencies,
):
    # arrange
    user_persistence = UserPersistenceDTO(
        public_id=uuid.uuid4(),
        email='email@email.com',
        hash_password='password-hashed',
        email_verified=False,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        last_login_at=None,
    )

    deps: SendEmailVerificationCodeDependencies = (
        send_email_verification_code_dependencies(user_persistence)
    )

    deps.uow.message_repo.create.side_effect = InfrastructureError(
        'Error attempting to persist verification code',
        InfrastructureErrorCode.DATABASE,
        Exception(),
    )

    use_case = SendEmailVerificationCodeUseCase(deps.user_repo, deps.uow)

    # act and arrange
    with pytest.raises(InfrastructureError):
        await use_case.execute(
            email='email@email.com',
            code_expiration_time=15,
            link='www.test.com/send-code',
            deadline=7,
        )

    # assert
    deps.user_repo.get_by_email.assert_called()
    deps.uow.__aenter__.assert_called()
    deps.uow.__aexit__.assert_called()
    deps.uow.code_repo.create.assert_called()
    deps.uow.message_repo.create.assert_called()
