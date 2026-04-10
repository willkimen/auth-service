import pytest

from domain.entities.user_factory import create_new_user
from domain.exceptions import InvalidEmailError, InvalidPasswordError


def test_create_new_user_success():
    user = create_new_user('user@email.com', 'Password!10')

    assert user.email.value == 'user@email.com'
    assert user.plain_password.value == 'Password!10'
    assert user.email_verified is False
    assert user.is_active is False
    assert user.last_login_at is None
    assert user.created_at == user.updated_at


def test_factory_rejects_invalid_email():
    with pytest.raises(InvalidEmailError):
        create_new_user('invalid', 'Password!10')


def test_factory_rejects_invalid_password():
    with pytest.raises(InvalidPasswordError):
        create_new_user('user@email.com', 'invalid')
