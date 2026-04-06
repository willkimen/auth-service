import pytest

from domain.exceptions import (
    InvalidEmailError,
    InvalidPasswordError,
)
from domain.user import User


# ========== change_password ===========
def test_password_changed_successfully(initial_state: dict):
    new_password = 'NewPassword!20'

    user = User(**initial_state)

    user.change_password(new_password)

    assert user.plain_password.value == new_password


def test_password_not_change_if_invalid(initial_state: dict):
    user = User(**initial_state)

    with pytest.raises(InvalidPasswordError):
        user.change_password('invalid')


def test_change_password_updated_user_state(initial_state: dict):
    user = User(**initial_state)
    previous_updated_at = user.updated_at

    user.change_password('NewPassword!20')

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_change_password_to_same_value_does_not_update_user_state(
    initial_state: dict,
):
    """
    Ensures that calling this method with the same value is idempotent.
    The method should not modify the state if the new password is equal
    to the current one. This is verified by asserting that updated_at
    remains unchanged after the second call.
    """
    same_password = 'NewPassword!10'
    user = User(**initial_state)

    user.change_password(same_password)
    updated_at_after_first_change = user.updated_at

    user.change_password(same_password)

    assert user.updated_at == updated_at_after_first_change


# ========== change_email ===========
def test_email_changed_successfully(initial_state: dict):
    new_email = 'newuser@email.com'

    user = User(**initial_state)
    user.change_email(new_email)

    assert user.email.value == new_email


def test_email_not_change_if_invalid(initial_state: dict):
    user = User(**initial_state)

    with pytest.raises(InvalidEmailError):
        user.change_email('invalid')


def test_change_email_update_user_state(initial_state: dict):
    user = User(**initial_state)
    previous_updated_at = user.updated_at

    user.change_email('newuser@email.com')

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_change_email_to_same_value_does_not_update_user_state(
    initial_state: dict,
):
    """
    Ensures that calling this method with the same value is idempotent.
    The method should not modify the state if the new email is equal
    to the current one. This is verified by asserting that updated_at
    remains unchanged after the second call.
    """
    user = User(**initial_state)

    same_email = 'NewEmail@email.com'
    user.change_email(same_email)
    updated_at_after_first_change = user.updated_at

    user.change_email(same_email)

    assert user.updated_at == updated_at_after_first_change


# ========== active ===========
def test_activate_user_successfully(initial_state: dict):
    user = User(**initial_state)
    assert not user.is_active

    user.activate()

    assert user.is_active


def test_activate_user_update_your_state(initial_state: dict):
    user = User(**initial_state)
    previous_updated_at = user.updated_at

    user.activate()

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_activate_an_active_user_does_not_change_your_state(
    initial_state: dict,
):
    """
    Ensures that calling activate multiple times is idempotent.
    Once the user is active, subsequent calls should not modify
    the state. This is verified by asserting that updated_at
    remains unchanged after the second call.
    """
    user = User(**initial_state)

    user.activate()
    updated_at_after_activation = user.updated_at

    user.activate()

    assert user.updated_at == updated_at_after_activation


# ========== deactivate ===========
def test_deactivate_user_successfully(initial_state: dict):
    initial_state['is_active'] = True
    user = User(**initial_state)

    user.deactivate()

    assert not user.is_active


def test_deactivate_user_update_user_state(initial_state: dict):
    initial_state['is_active'] = True
    user = User(**initial_state)
    previous_updated_at = user.updated_at

    user.deactivate()

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_deactivate_an_deactivated_user_does_not_change_your_state(
    initial_state: dict,
):
    """
    Ensures that calling deactivate multiple times is idempotent.
    Once the user is inactive, subsequent calls should not modify
    the state. This is verified by asserting that updated_at
    remains unchanged after the second call.
    """
    initial_state['is_active'] = True
    user = User(**initial_state)

    user.deactivate()
    updated_at_after_deactivation = user.updated_at

    user.deactivate()

    assert user.updated_at == updated_at_after_deactivation


# ========== mark_email_as_verified ===========
def test_verified_email_successfully(initial_state: dict):
    user = User(**initial_state)

    user.mark_email_as_verified()

    assert user.email_verified


def test_mark_email_as_verified_update_user_state(initial_state: dict):
    user = User(**initial_state)
    previous_updated_at = user.updated_at

    user.mark_email_as_verified()

    assert user.updated_at != previous_updated_at
    assert user.updated_at > previous_updated_at


def test_mark_an_already_verified_email_does_not_change_user_state(
    initial_state: dict,
):
    """
    Ensures that calling mark_email_as_verified multiple times is idempotent.
    Once the email is verified, subsequent calls should not modify the state.
    This is verified by asserting that updated_at remains unchanged after the
    second call.
    """
    user = User(**initial_state)

    user.mark_email_as_verified()
    updated_at_after_verification = user.updated_at

    user.mark_email_as_verified()

    assert user.updated_at == updated_at_after_verification


# ========== record_login ===========
def test_record_login_successfully(initial_state: dict):
    user = User(**initial_state)

    user.record_login()

    assert user.last_login_at is not None

    last_timestamp = user.last_login_at

    user.record_login()
    assert user.last_login_at != last_timestamp
