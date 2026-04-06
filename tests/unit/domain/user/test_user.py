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
def test_public_id_it_is_required(initial_state: dict):
    initial_state['public_id'] = None
    msg_error = 'public_id it is required'

    with pytest.raises(RequiredFieldError, match=msg_error):
        User(**initial_state)


def test_public_id_must_be_uuid_type(initial_state: dict):
    type_incorrect = 'type_incorrect'
    initial_state['public_id'] = type_incorrect
    msg_error = (
        f'Invalid id: expected UUID, got {type(type_incorrect).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        User(**initial_state)


# ============ email_verified =================
def test_email_verified_it_is_required(initial_state: dict):
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
def test_is_active_it_is_required(initial_state: dict):
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
    msg_error = 'created_at it is required'

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

    msg_error = 'updated_at it is required'
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
