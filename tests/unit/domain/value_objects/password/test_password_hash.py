from typing import cast

import pytest

from domain.exceptions import InvalidPasswordError
from domain.value_objects.password import PasswordHash

value_binary = b'1234357'


def test_password_hash_is_created_successfully():
    email = PasswordHash(value_binary)

    assert email.value == value_binary


def test_password_hash_objects_with_same_state_are_equals():
    hash = PasswordHash(value_binary)
    other_hash = PasswordHash(value_binary)

    assert hash == other_hash


def test_password_hash_should_not_be_none():
    msg_error = 'password hash cannot be empty'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordHash(cast(bytes, None))
