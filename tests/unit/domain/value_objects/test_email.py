from typing import cast

import pytest

from domain.exceptions import InvalidEmailError
from domain.value_objects import Email

correct_email = "user@email.com"


def test_email_is_created_successfully():
    email = Email(correct_email)

    assert email.value == correct_email


def test_email_objects_with_same_state_are_equals():
    email = Email(correct_email)
    other_email = Email(correct_email)

    assert email == other_email


def test_email_should_not_be_empty():
    invalid_inputs = ["", " "]

    for input in invalid_inputs:
        with pytest.raises(InvalidEmailError) as exc:
            Email(input)

        assert "email cannot be None or empty" in str(exc.value)


def test_email_should_not_be_none():
    with pytest.raises(InvalidEmailError) as exc:
        Email(cast(str, None))

    assert "email cannot be None or empty" in str(exc.value)


@pytest.mark.parametrize(
    "input",
    [
        "user@",
        "@email.com",
        "@email",
        "useremail.com",
        "user@email",
        "user@@email",
        "@@@.com",
        "@.com",
        "user b@c d.com",
        "abc!#$@email.com",
    ],
)
def test_email_should_not_be_in_an_invalid_format(input):
    with pytest.raises(InvalidEmailError) as exc:
        Email(input)

    assert "email must be in a valid format" in str(exc.value)
