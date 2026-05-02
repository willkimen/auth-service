from datetime import datetime, timedelta, timezone

import pytest

from domain.enums import CodeType
from domain.entities.verification_code import VerificationCode
from domain.exceptions import (
    MissingNewEmailError,
    VerificationCodeExpiredError
)

current_time = datetime.now(timezone.utc)


def test_create_code_success(initial_state: dict):
    code = VerificationCode(**initial_state)

    assert code.code is not None
    assert code.code.value == initial_state['code'].value
    assert code.user_public_id == initial_state['user_public_id']
    assert code.is_active(current_time)
    assert code.type == initial_state['type']
    assert code.payload is None
    assert code.expires_at == initial_state['expires_at']
    assert code.used_at is None
    assert not code.has_been_sent()


def test_create_code_with_payload_success(initial_state: dict):
    initial_state['payload'] = {'new_email': 'email@email.com'}
    initial_state['type'] = CodeType.CHANGE_EMAIL
    code = VerificationCode(**initial_state)

    assert code.payload is not None
    assert code.payload['new_email'] == 'email@email.com'
    assert code.get_new_email() == 'email@email.com'


def test_code_type_change_email_must_contain_new_email_in_payload(initial_state: dict):
    initial_state['type'] = CodeType.CHANGE_EMAIL
    msg_error = "CHANGE_EMAIL codes require 'new_email' in payload"

    with pytest.raises(MissingNewEmailError, match=msg_error):
        VerificationCode(**initial_state)


# ============= user_public_id ====================
def test_check_if_user_public_id_is_assigned_correctly(initial_state: dict):
    code = VerificationCode(**initial_state)
    assert code.user_public_id == initial_state['user_public_id']


def test_user_public_id_is_required(initial_state: dict):
    initial_state['user_public_id'] = None
    msg_error = 'user_public_id it is required'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


def test_user_public_id_must_be_correct_type(initial_state: dict):
    incorrect_type = 100
    initial_state['user_public_id'] = incorrect_type
    msg_error = (
        f'Invalid user_public_id: expected uuid type, '
        f'got {type(incorrect_type).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        VerificationCode(**initial_state)


# ============= type ====================
def test_check_if_type_code_is_assigned_correctly(initial_state: dict):
    code = VerificationCode(**initial_state)
    assert code.type == initial_state['type']


def test_type_code_is_required(initial_state: dict):
    initial_state['type'] = None
    msg_error = 'type it is required'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


def test_code_must_be_correct_type(initial_state: dict):
    incorrect_type = 'ACTIVE'
    initial_state['type'] = incorrect_type
    msg_error = (
        f'Invalid code type: expected CodeType, '
        f'got {type(incorrect_type).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        VerificationCode(**initial_state)


# ============= created_at ====================
def test_check_if_creation_date_is_assigned_correctly(initial_state: dict):
    code = VerificationCode(**initial_state)
    assert code.created_at == initial_state['created_at']


def test_creation_date_is_required(initial_state: dict):
    initial_state['created_at'] = None
    msg_error = 'created_at it is required'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


def test_creation_date_must_be_include_timezone_information(
    initial_state: dict,
):
    initial_state['created_at'] = datetime.now()
    msg_error = 'created_at must be timezone-aware'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


# ============= expires_at ====================
def test_check_if_expiration_date_is_assigned_correctly(initial_state: dict):
    code = VerificationCode(**initial_state)
    assert code.expires_at == initial_state['expires_at']


def test_expiration_date_is_required(initial_state: dict):
    initial_state['expires_at'] = None
    msg_error = 'expires_at it is required'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


def test_expiration_date_must_be_timezone_aware(initial_state: dict):
    initial_state['expires_at'] = datetime.now()
    msg_error = 'expires_at must be timezone-aware'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


def test_expiration_date_must_not_be_before_that_created_at(
    initial_state: dict,
):
    before = initial_state['created_at'] - timedelta(microseconds=1)
    initial_state['expires_at'] = before
    msg_error = 'expires_at must not be before created_at'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


# ============= used_at ====================
def test_check_if_usage_date_is_assigned_correctly(initial_state: dict):
    initial_state['used_at'] = datetime.now(timezone.utc)

    code = VerificationCode(**initial_state)

    assert code.used_at == initial_state['used_at']
    assert code.is_used()


def test_date_of_use_accept_none(initial_state: dict):
    initial_state['used_at'] = None

    code = VerificationCode(**initial_state)

    assert code.used_at is None
    assert not code.is_used()


def test_date_of_use_must_be_include_timezone_information(initial_state: dict):
    initial_state['used_at'] = datetime.now()
    msg_error = 'used_at must be timezone-aware'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


def test_date_of_use_must_not_be_before_that_creation_date(
    initial_state: dict,
):
    before = initial_state['created_at'] - timedelta(microseconds=1)
    initial_state['used_at'] = before
    msg_error = 'used_at must not be before created_at'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


# ============= is_active =====================
def test_code_unused_and_not_expired_is_active(initial_state: dict):
    user = VerificationCode(**initial_state)

    assert user.is_active(datetime.now(timezone.utc))


def test_code_used_but_not_expired_is_not_active(initial_state: dict):
    initial_state['used_at'] = datetime.now(timezone.utc)
    user = VerificationCode(**initial_state)

    assert not user.is_active(datetime.now(timezone.utc))

    # extra assert
    assert user.is_used()


def test_code_unused_but_expired_is_not_active(initial_state: dict):
    initial_state['expires_at'] = datetime.now(timezone.utc)

    user = VerificationCode(**initial_state)

    assert not user.is_active(datetime.now(timezone.utc))

    # extra assert
    assert user.is_expired(datetime.now(timezone.utc))


def test_code_used_and_expired_is_not_active(initial_state: dict):
    initial_state['used_at'] = datetime.now(timezone.utc)
    initial_state['expires_at'] = datetime.now(timezone.utc)

    user = VerificationCode(**initial_state)

    assert not user.is_active(datetime.now(timezone.utc))

    # extras asserts
    assert user.is_expired(datetime.now(timezone.utc))
    assert user.is_used()


def test_check_if_is_active_wait_date_with_timezone_information(
    initial_state: dict,
):
    user = VerificationCode(**initial_state)

    msg_error = 'now must be timezone-aware'
    with pytest.raises(ValueError, match=msg_error):
        user.is_active(datetime.now())


# ============= is_used =====================
def test_marking_as_used_should_guarantee_used_condition(initial_state: dict):
    user = VerificationCode(**initial_state)

    # previous state
    assert not user.is_used()

    user.mark_as_used(datetime.now(timezone.utc))

    assert user.is_used()

    # extra assert
    assert not user.is_active(datetime.now(timezone.utc))


# ============= mark_as_used =====================
def test_cannot_mark_as_used_expired_code(initial_state: dict):
    timestamp_expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    initial_state['expires_at'] = timestamp_expired

    user = VerificationCode(**initial_state)

    msg_error = 'code cannot be used because is has expired'
    with pytest.raises(VerificationCodeExpiredError, match=msg_error):
        user.mark_as_used(datetime.now(timezone.utc))


def test_mark_as_used_expect_timezone_date_information(initial_state: dict):
    user = VerificationCode(**initial_state)

    msg_error = 'used_at must be timezone-aware'
    with pytest.raises(ValueError, match=msg_error):
        user.mark_as_used(datetime.now())


def test_mark_as_used_cannot_be_earlier_than_creation_date(
    initial_state: dict,
):
    user = VerificationCode(**initial_state)

    before_created = initial_state['created_at'] - timedelta(microseconds=1)

    msg_error = 'used_at must not be before created_at'
    with pytest.raises(ValueError, match=msg_error):
        user.mark_as_used(before_created)


# ============= is_expired =====================
def test_code_expired_successfully(initial_state: dict):
    timestamp_expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    initial_state['expires_at'] = timestamp_expired

    user = VerificationCode(**initial_state)

    assert user.is_expired(datetime.now(timezone.utc))


def test_expiration_date_not_reached_code_not_expired(initial_state: dict):
    user = VerificationCode(**initial_state)

    assert not user.is_expired(datetime.now(timezone.utc))


def test_is_expired_expect_timezone_date_information(initial_state: dict):
    user = VerificationCode(**initial_state)

    msg_error = 'now must be timezone-aware'
    with pytest.raises(ValueError, match=msg_error):
        user.is_expired(datetime.now())


# ============= mark_as_sent =====================
def test_code_is_marked_as_sent_successfully(initial_state: dict):
    user = VerificationCode(**initial_state)

    assert not user.has_been_sent()

    user.mark_as_sent(current_time)

    assert user.has_been_sent()


def test_mark_as_sent_must_include_a_timezone_information(initial_state: dict):
    user = VerificationCode(**initial_state)

    msg_error = 'sent_at must be timezone-aware'
    with pytest.raises(ValueError, match=msg_error):
        user.mark_as_sent(datetime.now())


def test_mark_as_sent_cannot_be_earlier_than_creation_date(
    initial_state: dict,
):
    user = VerificationCode(**initial_state)

    before_created = initial_state['created_at'] - timedelta(microseconds=1)

    msg_error = 'sent_at must not be before created_at'
    with pytest.raises(ValueError, match=msg_error):
        user.mark_as_sent(before_created)
