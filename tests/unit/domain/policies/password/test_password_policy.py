from typing import cast

import pytest

from domain.exceptions import InvalidPasswordError
from domain.policies.password import PasswordPolicy

correct_password = 'PASSword1234!'


def test_plain_password_is_created_successfully():
    PasswordPolicy.validate(correct_password)


def test_password_should_not_be_none():
    msg_error = 'password cannot be empty'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordPolicy.validate(cast(str, None))


def test_password_should_not_be_empty():
    invalids_passwords = ['', ' ']
    msg_error = 'password cannot be empty'

    for password in invalids_passwords:
        with pytest.raises(InvalidPasswordError, match=msg_error):
            PasswordPolicy.validate(password)


def test_password_should_not_be_short():
    msg_error = 'password too short'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordPolicy.validate('Pa!1')


def test_password_should_not_be_so_long():
    msg_error = 'password too long'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordPolicy.validate('P!1a' * 33)


def test_password_should_contain_least_one_letter():
    msg_error = 'password must contain at least one letter'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordPolicy.validate('!1234567')


def test_password_should_contain_least_one_number():
    msg_error = 'password must contain at least one number'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordPolicy.validate('Password!')


def test_password_should_contain_least_one_special_character():
    msg_error = 'password must contain at least one special character'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordPolicy.validate('Password10')


def test_password_should_contain_least_one_uppercase_character():
    msg_error = 'password must contain at least one uppercase character'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordPolicy.validate('password!10')


def test_password_should_contain_least_one_lowercase_character():
    msg_error = 'password must contain at least one lowercase character'

    with pytest.raises(InvalidPasswordError, match=msg_error):
        PasswordPolicy.validate('PASSWORD!10')
