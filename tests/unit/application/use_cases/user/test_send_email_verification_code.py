import uuid
from datetime import datetime, timezone

import pytest

from application.dto.user_dto import UserPersistenceDTO
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
    UserNotFoundError,
)
from application.use_cases.user.send_email_verification_code import (
    SendEmailVerificationCodeUseCase,
)
from domain.exceptions import EmailAlreadyVerifiedError, InactiveUserError
from unit.application.use_cases.user.types import (
    SendEmailVerificationCodeDependencies,
)


async def test_initialize_email_verification_process_successfully(
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

    use_case = SendEmailVerificationCodeUseCase(deps.user_repo, deps.uow)

    # act
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
    deps.uow.publisher.publish.assert_called()


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
    deps.uow.publisher.publish.assert_not_called()


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
    deps.uow.publisher.publish.assert_not_called()


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
    deps.uow.publisher.publish.assert_not_called()


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
    deps.uow.publisher.publish.assert_not_called()


async def test_verification_process_not_initialize_when_event_publish_fails(
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

    deps.uow.publisher.publish.side_effect = InfrastructureError(
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
    deps.uow.publisher.publish.assert_called()
