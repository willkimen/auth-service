import pytest

from domain.exceptions import (
    InvalidEmailError,
    InvalidPasswordError,
)
from domain.user import User


# ========== change_password ===========
def test_password_changed_successfully(user_data_initial: dict):
    new_password = 'NewPassword!20'

    user = User(**user_data_initial)

    user.change_password(new_password)

    assert user.plain_password.value == new_password


def test_password_not_change_if_invalid(user_data_initial: dict):
    user = User(**user_data_initial)

    with pytest.raises(InvalidPasswordError):
        user.change_password('invalid')


def test_change_password_update_updated_at(user_data_initial: dict):
    user = User(**user_data_initial)
    previous_updated_at = user.updated_at

    user.change_password('NewPassword!20')

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_change_password_is_idempotent_for_same_value(user_data_initial: dict):
    """
    Ensures that calling this method with the same value is idempotent.
    The method should not modify the state if the new password is equal
    to the current one. This is verified by asserting that updated_at
    remains unchanged after the second call.
    """
    same_password = 'NewPassword!10'
    user = User(**user_data_initial)

    user.change_password(same_password)
    updated_at_after_first_change = user.updated_at

    user.change_password(same_password)

    assert user.updated_at == updated_at_after_first_change


# ========== change_email ===========
def test_email_changed_successfully(user_data_initial: dict):
    new_email = 'newuser@email.com'

    user = User(**user_data_initial)
    user.change_email(new_email)

    assert user.email.value == new_email


def test_email_not_change_if_invalid(user_data_initial: dict):
    user = User(**user_data_initial)

    with pytest.raises(InvalidEmailError):
        user.change_email('invalid')


def test_change_email_update_updated_at(user_data_initial: dict):
    user = User(**user_data_initial)
    previous_updated_at = user.updated_at

    user.change_email('newuser@email.com')

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_change_email_is_idempotent_for_same_value(user_data_initial: dict):
    """
    Ensures that calling this method with the same value is idempotent.
    The method should not modify the state if the new email is equal
    to the current one. This is verified by asserting that updated_at
    remains unchanged after the second call.
    """
    user = User(**user_data_initial)

    same_email = 'NewEmail@email.com'
    user.change_email(same_email)
    updated_at_after_first_change = user.updated_at

    user.change_email(same_email)

    assert user.updated_at == updated_at_after_first_change


# ========== active ===========
def test_activate_user_successfully(user_data_initial: dict):
    user = User(**user_data_initial)
    assert not user.is_active

    user.activate()

    assert user.is_active


def test_activate_update_updated_at(user_data_initial: dict):
    user = User(**user_data_initial)
    previous_updated_at = user.updated_at

    user.activate()

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_activate_user_is_idempotent(user_data_initial: dict):
    """
    Ensures that calling activate multiple times is idempotent.
    Once the user is active, subsequent calls should not modify
    the state. This is verified by asserting that updated_at
    remains unchanged after the second call.
    """
    user = User(**user_data_initial)

    user.activate()
    updated_at_after_activation = user.updated_at

    user.activate()

    assert user.updated_at == updated_at_after_activation


# ========== deactivate ===========
def test_deactivate_user_successfully(user_data_initial: dict):
    user_data_initial['is_active'] = True
    user = User(**user_data_initial)

    user.deactivate()

    assert not user.is_active


def test_deactivate_update_updated_at(user_data_initial: dict):
    user_data_initial['is_active'] = True
    user = User(**user_data_initial)
    previous_updated_at = user.updated_at

    user.deactivate()

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_deactivate_user_is_idempotent(user_data_initial: dict):
    """
    Ensures that calling deactivate multiple times is idempotent.
    Once the user is inactive, subsequent calls should not modify
    the state. This is verified by asserting that updated_at
    remains unchanged after the second call.
    """
    user_data_initial['is_active'] = True
    user = User(**user_data_initial)

    user.deactivate()
    updated_at_after_deactivation = user.updated_at

    user.deactivate()

    assert user.updated_at == updated_at_after_deactivation


# ========== mark_email_as_verified ===========
def test_verified_email_successfully(user_data_initial: dict):
    user = User(**user_data_initial)

    user.mark_email_as_verified()

    assert user.email_verified


def test_mark_email_as_verified_update_updated_at(user_data_initial: dict):
    user = User(**user_data_initial)
    previous_updated_at = user.updated_at

    user.mark_email_as_verified()

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_mark_email_as_verified_is_idempotent(user_data_initial: dict):
    """
    Ensures that calling mark_email_as_verified multiple times is idempotent.
    Once the email is verified, subsequent calls should not modify the state.
    This is verified by asserting that updated_at remains unchanged after the
    second call.
    """
    user = User(**user_data_initial)

    user.mark_email_as_verified()
    updated_at_after_verification = user.updated_at

    user.mark_email_as_verified()

    assert user.updated_at == updated_at_after_verification


# ========== record_login ===========
def test_record_login_successfully(user_data_initial: dict):
    user = User(**user_data_initial)

    user.record_login()

    assert user.last_login_at is not None

    last_timestamp = user.last_login_at

    user.record_login()
    assert user.last_login_at != last_timestamp
