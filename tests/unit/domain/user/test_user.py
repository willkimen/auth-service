from datetime import datetime, timedelta, timezone

import pytest

from domain.exceptions import (
        InvalidEmailError,
        InvalidPasswordError,
        InvalidTimestampError,
)
from domain.user import User


def test_create_user_success(user_data_initial: dict):
    user = User(**user_data_initial)

    assert user.public_id == user_data_initial["public_id"]
    assert user.plain_password.value == user_data_initial["plain_password"]
    assert user.email.value == user_data_initial["email"]
    assert user.email_verified == user_data_initial["email_verified"]
    assert user.is_active == user_data_initial["is_active"]
    assert user.created_at == user_data_initial["created_at"]
    assert user.updated_at == user_data_initial["updated_at"]
    assert user.created_at == user.updated_at
    assert user.last_login_at == user_data_initial["last_login_at"]


# ============ email =================
def test_user_constructor_rejects_invalid_email(user_data_initial: dict):
    user_data_initial["email"] = "invalid"

    with pytest.raises(InvalidEmailError):
        User(**user_data_initial)


# ============ plain_password =================
def test_user_constructor_rejects_invalid_password(user_data_initial: dict):
    user_data_initial["plain_password"] = "invalid"

    with pytest.raises(InvalidPasswordError):
        User(**user_data_initial)


# ============ created_at =================
def test_user_constructor_rejects_created_at_when_is_none(
        user_data_initial: dict
):
    user_data_initial["created_at"] = None

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "created_at must not be None" in str(e)


def test_user_constructor_rejects_created_at_when_is_not_aware(
        user_data_initial: dict
):
    datetime_not_aware = datetime.now()
    user_data_initial["created_at"] = datetime_not_aware

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "created_at must be timezone-aware" in str(e)


def test_user_constructor_rejects_created_at_when_it_be_in_future(
        user_data_initial: dict
):
    future_date = user_data_initial["created_at"] + timedelta(seconds=1)
    user_data_initial["created_at"] = future_date

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "created_at must not be in the future" in str(e)


# ============ updated_at =================
def test_user_constructor_rejects_updated_at_when_it_is_none(
        user_data_initial: dict
):
    user_data_initial["updated_at"] = None

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "updated_at must not be None" in str(e)


def test_user_constructor_rejects_updated_at_when_is_not_aware(
        user_data_initial: dict
):
    datetime_not_aware = datetime.now()
    user_data_initial["updated_at"] = datetime_not_aware

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "updated_at must be timezone-aware" in str(e)


def test_user_constructor_rejects_updated_at_when_it_be_in_future(
        user_data_initial: dict
):
    future_date = user_data_initial["updated_at"] + timedelta(seconds=1)
    user_data_initial["updated_at"] = future_date

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "updated_at must not be in the future" in str(e)


def test_user_constructor_rejects_updated_at_when_it_be_before_created_at(
        user_data_initial: dict
):
    before_created_at = user_data_initial["created_at"] - timedelta(seconds=1)
    user_data_initial["updated_at"] = before_created_at

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "updated_at must not be before created_at" in str(e)


# ============== last_login_at =============
def test_user_constructor_rejects_last_login_at_when_is_not_aware(
        user_data_initial: dict
):
    datetime_not_aware = datetime.now()
    user_data_initial["last_login_at"] = datetime_not_aware

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "last_login_at must be timezone-aware" in str(e)


def test_user_constructor_rejects_last_login_at_when_it_be_in_future(
        user_data_initial: dict
):
    user_data_initial["last_login_at"] = datetime.now(timezone.utc)

    future_date = user_data_initial["last_login_at"] + timedelta(seconds=1)
    user_data_initial["last_login_at"] = future_date

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "last_login_at must not be in the future" in str(e)


def test_user_constructor_rejects_last_login_at_when_it_be_before_created_at(
        user_data_initial: dict
):
    before_created_at = user_data_initial["created_at"] - timedelta(seconds=1)
    user_data_initial["last_login_at"] = before_created_at

    with pytest.raises(InvalidTimestampError) as e:
        User(**user_data_initial)

    assert "last_login_at must not be before created_at" in str(e)
