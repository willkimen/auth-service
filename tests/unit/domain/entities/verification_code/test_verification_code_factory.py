import uuid
from datetime import datetime, timedelta, timezone

import pytest

from domain.entities.verification_code_factory import (
    new_change_email_code,
    new_change_password_code,
    new_delete_account_code,
    new_email_verification_code,
    new_reset_password_code,
)
from domain.enums import CodeType
from domain.exceptions import InvalidEmailError
from domain.value_objects.code import Code

user_id = uuid.uuid4()
created_at = datetime.now(timezone.utc)
expires_at = created_at + timedelta(days=7)
new_email = 'user@email.com'
incorrect_format_email = 'email.com'
current_time = datetime.now(timezone.utc)
new_code = Code.generate()


def test_create_code_success():
    code = new_email_verification_code(
        user_id, new_code, created_at, expires_at, None
    )

    assert code.code is not None
    assert code.code.value == new_code.value
    assert code.user_id == user_id
    assert code.is_active(current_time)
    assert code.type == CodeType.EMAIL_VERIFICATION
    assert not code.has_new_email()
    assert code.payload is None
    assert code.created_at == created_at
    assert code.expires_at == expires_at
    assert code.used_at is None
    assert not code.has_been_sent()


def test_create_change_email_code_success():
    code = new_change_email_code(
        user_id,
        new_code,
        created_at,
        expires_at,
        None,
        new_email,
    )

    assert code.code is not None
    assert code.code.value == new_code.value
    assert code.user_id == user_id
    assert code.is_active(current_time)
    assert code.type == CodeType.CHANGE_EMAIL
    assert code.has_new_email()
    assert code.payload is not None
    assert code.payload['new_email'] == new_email
    assert code.created_at == created_at
    assert code.expires_at == expires_at
    assert code.used_at is None
    assert not code.has_been_sent()


def test_create_change_password_code_success():
    code = new_change_password_code(
        user_id, new_code, created_at, expires_at, None
    )

    assert code.code is not None
    assert code.code.value == new_code.value
    assert code.user_id == user_id
    assert code.is_active(current_time)
    assert code.type == CodeType.CHANGE_PASSWORD
    assert not code.has_new_email()
    assert code.payload is None
    assert code.created_at == created_at
    assert code.expires_at == expires_at
    assert code.used_at is None
    assert not code.has_been_sent()


def test_create_reset_password_code_success():
    code = new_reset_password_code(
        user_id, new_code, created_at, expires_at, None
    )

    assert code.code is not None
    assert code.code.value == new_code.value
    assert code.user_id == user_id
    assert code.is_active(current_time)
    assert code.type == CodeType.RESET_PASSWORD
    assert not code.has_new_email()
    assert code.payload is None
    assert code.created_at == created_at
    assert code.expires_at == expires_at
    assert code.used_at is None
    assert not code.has_been_sent()


def test_create_delete_account_code_success():
    code = new_delete_account_code(
        user_id, new_code, created_at, expires_at, None
    )

    assert code.code is not None
    assert code.code.value == new_code.value
    assert code.user_id == user_id
    assert code.is_active(current_time)
    assert code.type == CodeType.DELETE_ACCOUNT
    assert not code.has_new_email()
    assert code.payload is None
    assert code.created_at == created_at
    assert code.expires_at == expires_at
    assert code.used_at is None
    assert not code.has_been_sent()


def test_email_payload_must_be_in_valid_format():
    with pytest.raises(InvalidEmailError):
        new_change_email_code(
            user_id,
            new_code,
            created_at,
            expires_at,
            None,
            incorrect_format_email,
        )
