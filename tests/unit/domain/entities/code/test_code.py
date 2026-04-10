from datetime import datetime, timedelta, timezone

import pytest

from domain.entities.code import VerificationCode
from domain.exceptions import (
    CodeStatusError,
    CodeTypeError,
    InvalidTimestampError,
    RequiredFieldError,
)

current_time = datetime.now(timezone.utc)


def test_create_code_success(initial_state: dict):
    code = VerificationCode(**initial_state)

    assert code.code is not None
    assert code.user_id == initial_state['user_id']
    assert code.is_active(current_time)
    assert code.type == initial_state['type']
    assert not code.has_new_email()
    assert code.payload is None
    assert code.expires_at == initial_state['expires_at']
    assert code.used_at is None


def test_create_code_with_payload_success(initial_state: dict):
    initial_state['payload'] = {'new_email': 'email@email.com'}
    code = VerificationCode(**initial_state)

    assert code.code is not None
    assert code.user_id == initial_state['user_id']
    assert code.is_active(current_time)
    assert code.type == initial_state['type']
    assert code.has_new_email()
    assert code.payload is not None
    assert code.payload['new_email'] == 'email@email.com'
    assert code.expires_at == initial_state['expires_at']
    assert code.used_at is None


# ============= code ====================
def test_should_return_same_code_when_code_is_provided(initial_state: dict):
    expected_code = '012345'
    initial_state['code'] = expected_code

    code = VerificationCode(**initial_state)

    assert code.code == expected_code


def test_code_must_be_string_type(initial_state: dict):
    incorrect_type = 123456
    initial_state['code'] = incorrect_type
    msg_error = (
        f'Invalid code: expected str, got {type(incorrect_type).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        VerificationCode(**initial_state)


def test_code_must_not_be_empty_string(initial_state: dict):
    empty = ' '
    initial_state['code'] = empty
    msg_error = 'code cannot be empty'

    with pytest.raises(ValueError, match=msg_error):
        VerificationCode(**initial_state)


# ============= user_id ====================
def test_user_id_it_is_required(initial_state: dict):
    initial_state['user_id'] = None
    msg_error = 'user_id it is required'

    with pytest.raises(RequiredFieldError, match=msg_error):
        VerificationCode(**initial_state)


def test_user_id_must_be_int_type(initial_state: dict):
    incorrect_type = '100'
    initial_state['user_id'] = incorrect_type
    msg_error = (
        f'Invalid id: expected int, got {type(incorrect_type).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        VerificationCode(**initial_state)


# ============= type ====================
def test_type_it_is_required(initial_state: dict):
    initial_state['type'] = None
    msg_error = 'type it is required'

    with pytest.raises(RequiredFieldError, match=msg_error):
        VerificationCode(**initial_state)


def test_type_must_be_codetype_type(initial_state: dict):
    incorrect_type = 'ACTIVE'
    initial_state['type'] = incorrect_type
    msg_error = (
        f'Invalid code type: expected CodeType, '
        f'got {type(incorrect_type).__name__}'
    )

    with pytest.raises(CodeTypeError, match=msg_error):
        VerificationCode(**initial_state)


# ============= created_at ====================
def test_created_at_it_is_required(initial_state: dict):
    initial_state['created_at'] = None
    msg_error = 'created_at it is required'

    with pytest.raises(RequiredFieldError, match=msg_error):
        VerificationCode(**initial_state)


def test_created_at_must_be_timezone_aware(initial_state: dict):
    initial_state['created_at'] = datetime.now()
    msg_error = 'created_at must be timezone-aware'

    with pytest.raises(InvalidTimestampError, match=msg_error):
        VerificationCode(**initial_state)


def test_created_at_must_not_be_in_future(initial_state: dict):
    in_future = datetime.now(timezone.utc) + timedelta(seconds=5)
    initial_state['created_at'] = in_future
    msg_error = 'created_at must not be in the future'

    with pytest.raises(InvalidTimestampError, match=msg_error):
        VerificationCode(**initial_state)


# ============= expires_at ====================
def test_expires_at_it_is_required(initial_state: dict):
    initial_state['expires_at'] = None
    msg_error = 'expires_at it is required'

    with pytest.raises(RequiredFieldError, match=msg_error):
        VerificationCode(**initial_state)


def test_expires_at_must_be_timezone_aware(initial_state: dict):
    initial_state['expires_at'] = datetime.now()
    msg_error = 'expires_at must be timezone-aware'

    with pytest.raises(InvalidTimestampError, match=msg_error):
        VerificationCode(**initial_state)


def test_expires_at_must_not_be_before_that_created_at(initial_state: dict):
    before = initial_state['created_at'] - timedelta(microseconds=1)
    initial_state['expires_at'] = before
    msg_error = 'expires_at must not be before created_at'

    with pytest.raises(InvalidTimestampError, match=msg_error):
        VerificationCode(**initial_state)


# ============= used_at ====================
def test_used_at_accept_none(initial_state: dict):
    initial_state['used_at'] = None

    code = VerificationCode(**initial_state)

    assert code.used_at is None
    assert not code.is_used()


def test_should_return_same_used_at_when_is_provided(initial_state: dict):
    initial_state['used_at'] = datetime.now(timezone.utc)

    code = VerificationCode(**initial_state)

    assert code.used_at == initial_state['used_at']
    assert code.is_used()


def test_used_at_must_be_timezone_aware(initial_state: dict):
    initial_state['used_at'] = datetime.now()
    msg_error = 'used_at must be timezone-aware'

    with pytest.raises(InvalidTimestampError, match=msg_error):
        VerificationCode(**initial_state)


def test_used_at_must_not_be_before_that_created_at(initial_state: dict):
    before = initial_state['created_at'] - timedelta(microseconds=1)
    initial_state['used_at'] = before
    msg_error = 'used_at must not be before created_at'

    with pytest.raises(InvalidTimestampError, match=msg_error):
        VerificationCode(**initial_state)


# ============= is_active =====================
def test_is_active_returns_true_when_not_used_and_not_expired(
    initial_state: dict,
):
    user = VerificationCode(**initial_state)

    assert user.is_active(datetime.now(timezone.utc))


def test_is_active_returns_false_when_used_and_not_expired(
    initial_state: dict,
):
    initial_state['used_at'] = datetime.now(timezone.utc)
    user = VerificationCode(**initial_state)

    assert not user.is_active(datetime.now(timezone.utc))

    # extra assert
    assert user.is_used()


def test_is_active_returns_false_when_not_used_and_expired(
    initial_state: dict,
):
    initial_state['expires_at'] = datetime.now(timezone.utc)

    user = VerificationCode(**initial_state)

    assert not user.is_active(datetime.now(timezone.utc))

    # extra assert
    assert user.is_expired(datetime.now(timezone.utc))


def test_is_active_returns_false_when_used_and_expired(initial_state: dict):
    initial_state['used_at'] = datetime.now(timezone.utc)
    initial_state['expires_at'] = datetime.now(timezone.utc)

    user = VerificationCode(**initial_state)

    assert not user.is_active(datetime.now(timezone.utc))

    # extras asserts
    assert user.is_expired(datetime.now(timezone.utc))
    assert user.is_used()


def test_is_active_expect_timestamp_aware(initial_state: dict):
    user = VerificationCode(**initial_state)

    msg_error = 'now must be timezone-aware'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        user.is_active(datetime.now())


# ============= is_used =====================
def test_is_used_returns_true_when_marked_used(initial_state: dict):
    user = VerificationCode(**initial_state)

    # previous state
    assert not user.is_used()

    user.mark_as_used(datetime.now(timezone.utc))

    assert user.is_used()

    # extra assert
    assert not user.is_active(datetime.now(timezone.utc))


def test_is_used_returns_false_when_not_marked_used(initial_state: dict):
    user = VerificationCode(**initial_state)

    assert not user.is_used()

    # extra assert
    assert user.is_active(datetime.now(timezone.utc))


# ============= mark_as_used =====================
def test_mark_as_used_raise_exception_when_already_used(initial_state: dict):
    user = VerificationCode(**initial_state)

    # already used
    user.mark_as_used(datetime.now(timezone.utc))

    msg_error = 'code cannot be used'
    with pytest.raises(CodeStatusError, match=msg_error):
        user.mark_as_used(datetime.now(timezone.utc))


def test_mark_as_used_raise_exception_when_expired_code(initial_state: dict):
    timestamp_expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    initial_state['expires_at'] = timestamp_expired

    user = VerificationCode(**initial_state)

    msg_error = 'code cannot be used'
    with pytest.raises(CodeStatusError, match=msg_error):
        user.mark_as_used(datetime.now(timezone.utc))


def test_mark_as_used_expect_timestamp_aware(initial_state: dict):
    user = VerificationCode(**initial_state)

    msg_error = 'now must be timezone-aware'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        user.mark_as_used(datetime.now())


# ============= is_expired =====================
def test_is_expired_returns_true_if_expired_code(initial_state: dict):
    timestamp_expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    initial_state['expires_at'] = timestamp_expired

    user = VerificationCode(**initial_state)

    assert user.is_expired(datetime.now(timezone.utc))


def test_is_expired_returns_false_if_not_expired_code(initial_state: dict):
    user = VerificationCode(**initial_state)

    assert not user.is_expired(datetime.now(timezone.utc))


def test_is_expired_expect_timestamp_aware(initial_state: dict):
    user = VerificationCode(**initial_state)

    msg_error = 'now must be timezone-aware'
    with pytest.raises(InvalidTimestampError, match=msg_error):
        user.is_expired(datetime.now())
