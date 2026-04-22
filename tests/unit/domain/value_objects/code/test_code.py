from typing import cast

import pytest

from domain.exceptions import InvalidCodeError
from domain.value_objects.code import Code


def test_code_is_generated_correctly():
    expected_number_digits = 6

    code = Code.generate()

    assert len(code.value) == expected_number_digits
    assert code.value.isdigit()


def test_code_with_same_state_are_equals():
    code = Code('123456')
    other_code = Code('123456')

    assert code == other_code


def test_code_must_be_string_type():
    incorrect_type = 123456
    msg_error = (
        f'Invalid code: expected str, got {type(incorrect_type).__name__}'
    )

    with pytest.raises(TypeError, match=msg_error):
        Code(cast(str, incorrect_type))


def test_code_must_not_be_empty_string():
    msg_error = 'code cannot be empty'

    with pytest.raises(ValueError, match=msg_error):
        Code('')


def test_code_must_be_only_numeric_digits():
    msg_error = 'code must be a 6-digit numeric string'
    with pytest.raises(InvalidCodeError, match=msg_error):
        Code('1234x6')


def test_code_must_contain_correct_number_digits():
    msg_error = 'code must be a 6-digit numeric string'
    with pytest.raises(InvalidCodeError, match=msg_error):
        Code('12345')

    with pytest.raises(InvalidCodeError, match=msg_error):
        Code('1234567')
