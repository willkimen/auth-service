from domain.entities.user_factory import create_new_user
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash

hash_password = PasswordHash(b'somepassword')
email = Email('user@email.com')


def test_create_new_user_success():
    user = create_new_user(email, hash_password)

    assert user.email.value == email.value
    assert user.hash_password.value == hash_password.value
    assert user.email_verified is False
    assert user.is_active is True
    assert user.last_login_at is None
    assert user.created_at == user.updated_at
