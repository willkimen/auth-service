from typing import cast

import pytest

from domain.exceptions import InvalidPasswordError
from domain.value_objects import PlainPassword

correct_password = "PASSword1234!"


def test_plain_password_is_created_successfully():
    email = PlainPassword(correct_password)

    assert email.value == correct_password


def test_plain_password_objects_with_same_state_are_equals():
    password = PlainPassword(correct_password)
    other = PlainPassword(correct_password)

    assert password == other


def test_password_should_not_be_none():
    with pytest.raises(InvalidPasswordError) as exc:
        PlainPassword(cast(str, None))

    assert "password cannot be empty" in str(exc.value)


def test_password_should_not_be_empty():
    invalids_passwords = ["", " "]

    for password in invalids_passwords:
        with pytest.raises(InvalidPasswordError) as exc:
            PlainPassword(password)

        assert "password cannot be empty" in str(exc.value)


def test_password_should_not_be_short():
    with pytest.raises(InvalidPasswordError) as exc:
        PlainPassword("Pa!1")

    assert "password too short" in str(exc.value)


def test_password_should_not_be_so_long():
    with pytest.raises(InvalidPasswordError) as exc:
        PlainPassword("P!1a" * 33)

    assert "password too long" in str(exc.value)


def test_password_should_contain_least_one_letter():
    with pytest.raises(InvalidPasswordError) as exc:
        PlainPassword("!1234567")

    assert "password must contain at least one letter" in str(exc.value)


def test_password_should_contain_least_one_number():
    with pytest.raises(InvalidPasswordError) as exc:
        PlainPassword("Password!")

    assert "password must contain at least one number" in str(exc.value)


def test_password_should_contain_least_one_special_character():
    with pytest.raises(InvalidPasswordError) as exc:
        PlainPassword("Password10")

    assert (
        "password must contain at least "
        "one special character"
    ) in str(exc.value)


def test_password_should_contain_least_one_uppercase_character():
    with pytest.raises(InvalidPasswordError) as exc:
        PlainPassword("password!10")

    assert (
        "password must contain at least "
        "one uppercase character"
    ) in str(exc.value)


def test_password_should_contain_least_one_lowercase_character():
    with pytest.raises(InvalidPasswordError) as exc:
        PlainPassword("PASSWORD!10")

    assert (
        "password must contain at least "
        "one lowercase character"
    ) in str(exc.value)
