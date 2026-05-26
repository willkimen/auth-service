import bcrypt
import pytest

from adapters.outputs.hashers.bcrypt_hasher import BcryptHasher
from application.exceptions import InfrastructureError, InfrastructureErrorCode

raw_password = 'fakepassword'


def test_hash_password_successfully():
    hasher = BcryptHasher()

    hashed: str = hasher.hash(raw_password)

    assert isinstance(hashed, str)
    assert len(hashed) > 0
    assert hasher.verify_password(raw_password, hashed)


def test_hash_raises_infrastructure_error_on_invalid_input_type():
    hasher = BcryptHasher()

    with pytest.raises(InfrastructureError) as e:
        hasher.hash(b'fakepassword')  # type: ignore

    error = e.value
    assert error.code == InfrastructureErrorCode.PASSWORD_HASHER
    assert isinstance(error.cause, AttributeError)
    assert 'password hashing service' in str(error)


def test_hash_raises_infrastructure_error_on_cryptographic_failure(
    monkeypatch,
):
    hasher = BcryptHasher()
    senha_plana = 'MinhaSenha123'

    def mock_hashpw(*args, **kwargs):
        raise ValueError('Invalid salt format')

    monkeypatch.setattr(bcrypt, 'hashpw', mock_hashpw)

    with pytest.raises(InfrastructureError) as e:
        hasher.hash(senha_plana)

    error = e.value
    assert error.code == InfrastructureErrorCode.PASSWORD_HASHER
    assert isinstance(error.cause, ValueError)
    assert 'password hashing service' in str(error)


def test_verify_password_raises_infrastructure_error_on_cryptographic_failure(
    monkeypatch,
):
    hasher = BcryptHasher()

    def mock_checkpw(*args, **kwargs):
        raise ValueError('Invalid salt prefix')

    monkeypatch.setattr(bcrypt, 'checkpw', mock_checkpw)

    with pytest.raises(InfrastructureError) as e:
        hasher.verify_password('qualquer_senha', 'qualquer_hash')

    error = e.value
    assert error.code == InfrastructureErrorCode.PASSWORD_HASHER
    assert isinstance(error.cause, ValueError)
    assert 'Password verification failure' in str(error)
