import uuid
from datetime import datetime, timedelta, timezone

import pytest

from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.value_objects.code import Code
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash

# for user
public_id = uuid.uuid4()
email = Email('email@email.com')
password_hash = PasswordHash('password-hashed')
created_at = datetime.now(timezone.utc)
updated_at = datetime.now(timezone.utc)

# for verification code
code = Code.generate()
correct_code_type = CodeType.EMAIL_VERIFICATION
code_not_expired = created_at + timedelta(minutes=15)
code_expired = datetime.now(timezone.utc) + +timedelta(milliseconds=1)
code_not_used = None
code_used = datetime.now(timezone.utc)
code_not_sent = None


@pytest.fixture
def active_user() -> User:
    return User(
        public_id=public_id,
        email=email,
        hash_password=password_hash,
        email_verified=False,
        is_active=True,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=None,
    )


@pytest.fixture
def unverified_user() -> User:
    return User(
        public_id=public_id,
        email=email,
        hash_password=password_hash,
        email_verified=False,
        is_active=True,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=None,
    )


@pytest.fixture
def verified_user() -> User:
    return User(
        public_id=public_id,
        email=email,
        hash_password=password_hash,
        email_verified=True,
        is_active=True,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=None,
    )


@pytest.fixture
def inactive_user() -> User:
    return User(
        public_id=public_id,
        email=email,
        hash_password=password_hash,
        email_verified=False,
        is_active=False,
        created_at=created_at,
        updated_at=updated_at,
        last_login_at=None,
    )


@pytest.fixture
def create_unused_code():
    def _create(
        code_type: CodeType,
        payload: dict | None = None,
    ) -> VerificationCode:
        return VerificationCode(
            code=code,
            user_public_id=public_id,
            type=code_type,
            created_at=created_at,
            expires_at=code_not_expired,
            used_at=code_not_used,
            sent_at=code_not_sent,
            payload=payload,
        )

    return _create


@pytest.fixture
def create_used_code():
    def _create(
        code_type: CodeType,
        payload: dict | None = None,
    ) -> VerificationCode:
        return VerificationCode(
            code=code,
            user_public_id=public_id,
            type=code_type,
            created_at=created_at,
            expires_at=code_not_expired,
            used_at=code_used,
            sent_at=code_not_sent,
            payload=payload,
        )

    return _create


@pytest.fixture
def create_expired_code():
    def _create(
        code_type: CodeType,
        payload: dict | None = None,
    ) -> VerificationCode:
        return VerificationCode(
            code=code,
            user_public_id=public_id,
            type=code_type,
            created_at=created_at,
            expires_at=code_expired,
            used_at=code_not_used,
            sent_at=code_not_sent,
            payload=payload,
        )

    return _create
