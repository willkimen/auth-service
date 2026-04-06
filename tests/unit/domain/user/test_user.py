from datetime import datetime, timedelta, timezone

import pytest

from domain.exceptions import (
    InvalidEmailError,
    InvalidPasswordError,
    InvalidTimestampError,
    RequiredFieldError,
)
from domain.user import User


def test_create_user_success(initial_state: dict):
    user = User(**initial_state)

    assert user.public_id == initial_state['public_id']
    assert user.plain_password.value == initial_state['plain_password']
    assert user.email.value == initial_state['email']
    assert user.email_verified == initial_state['email_verified']
    assert user.is_active == initial_state['is_active']
    assert user.created_at == initial_state['created_at']
    assert user.updated_at == initial_state['updated_at']
    assert user.created_at == user.updated_at
    assert user.last_login_at == initial_state['last_login_at']


# ============ public_id =================
def test_public_id_must_not_be_none(initial_state: dict):
    initial_state['public_id'] = None
    msg_error = 'public_id it is required'

    with pytest.raises(RequiredFieldError, match=msg_error):
        User(**initial_state)


def test_public_id_must_be_uuid_type(initial_state: dict):
    type_incorrect = 'type_incorrect'
    initial_state['public_id'] = type_incorrect
    msg_error = (
            'Invalid id: expected UUID, '
            f'got {type(type_incorrect).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        User(**initial_state)


# ============ email_verified =================
def test_email_verified_must_not_be_none(initial_state: dict):
    initial_state['email_verified'] = None
    msg_error = 'email_verified it is required'

    with pytest.raises(RequiredFieldError, match=msg_error):
        User(**initial_state)


def test_email_verified_must_be_bool_type(initial_state: dict):
    type_incorrect = 0
    initial_state['email_verified'] = type_incorrect
    msg_error = (
            'Invalid email_verified: expected bool, '
            f'got {type(type_incorrect).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        User(**initial_state)


# ============ is_active =================
def test_is_active_must_not_be_none(initial_state: dict):
    initial_state['is_active'] = None
    msg_error = 'is_active it is required'

    with pytest.raises(RequiredFieldError, match=msg_error):
        User(**initial_state)


def test_is_active_must_be_bool_type(initial_state: dict):
    type_incorrect = 0
    initial_state['is_active'] = type_incorrect
    msg_error = (
            'Invalid is_active: expected bool, '
            f'got {type(type_incorrect).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        User(**initial_state)


# ============ email =================
def test_email_with_invalid_format_is_not_accepted(initial_state: dict):
    initial_state['email'] = 'invalid'

    with pytest.raises(InvalidEmailError):
        User(**initial_state)


# ============ plain_password =================
def test_password_invalid_is_not_accepted(initial_state: dict):
    initial_state['plain_password'] = 'invalid'

    with pytest.raises(InvalidPasswordError):
        User(**initial_state)


# ============ created_at =================
def test_user_must_have_an_creation_date(initial_state: dict):
    initial_state['created_at'] = None

    msg_error = 'created_at must not be None'
    with pytest.raises(RequiredFieldError, match=msg_error):
        User(**initial_state)


def test_creation_date_must_include_a_timezone_information(
    initial_state: dict,
):
    without_timezone = datetime.now()
    initial_state['created_at'] = without_timezone

    msg_error = 'created_at must be timezone-aware'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        User(**initial_state)


def test_creation_date_cannot_be_in_the_future(initial_state: dict):
    future_date = datetime.now(timezone.utc) + timedelta(seconds=1)
    initial_state['created_at'] = future_date

    msg_error = 'created_at must not be in the future'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        User(**initial_state)


# ============ updated_at =================
def test_user_must_have_an_update_date(initial_state: dict):
    initial_state['updated_at'] = None

    msg_error = 'updated_at must not be None'
    with pytest.raises(RequiredFieldError, match=msg_error):
        User(**initial_state)


def test_update_date_must_include_a_timezone_information(
    initial_state: dict,
):
    without_timezone = datetime.now()
    initial_state['updated_at'] = without_timezone

    msg_error = 'updated_at must be timezone-aware'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        User(**initial_state)


def test_update_date_cannot_be_in_the_future(initial_state: dict):
    future_date = datetime.now(timezone.utc) + timedelta(seconds=1)
    initial_state['updated_at'] = future_date

    msg_error = 'updated_at must not be in the future'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        User(**initial_state)


def test_update_date_cannot_be_earlier_than_creation_date(
    initial_state: dict,
):
    before_created_at = initial_state['created_at'] - timedelta(seconds=1)
    initial_state['updated_at'] = before_created_at

    msg_error = 'updated_at must not be before created_at'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        User(**initial_state)


# ============== last_login_at =============
def test_last_login_date_must_include_a_timezone_information(
    initial_state: dict,
):
    without_timezone = datetime.now()
    initial_state['last_login_at'] = without_timezone

    msg_error = 'last_login_at must be timezone-aware'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        User(**initial_state)


def test_last_login_date_cannot_be_in_the_future(initial_state: dict):
    future_date = datetime.now(timezone.utc) + timedelta(seconds=1)
    initial_state['last_login_at'] = future_date

    msg_error = 'last_login_at must not be in the future'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        User(**initial_state)


def test_last_login_date_cannot_be_earlier_than_creation_date(
    initial_state: dict,
):
    before_created_at = initial_state['created_at'] - timedelta(seconds=1)
    initial_state['last_login_at'] = before_created_at

    msg_error = 'last_login_at must not be before created_at'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        User(**initial_state)
