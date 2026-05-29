import uuid

import jwt
import pytest

from adapters.outputs.token.pyjwt_manager import PyJWTManagerAdapter
from application.dtos.token_dto import PayloadTokenDTO
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidTokenError,
    InvalidTokenErrorCode,
)

sub = uuid.uuid4()


def test_return_payload_dto_when_token_is_valid():
    # arrange
    manager = PyJWTManagerAdapter(key='secret-key')

    token = manager.new_access(sub)

    # act
    payload = manager.validate(token)

    # asserts
    assert isinstance(payload, PayloadTokenDTO)

    assert payload.sub == str(sub)
    assert payload.typ == 'access'

    assert payload.jti
    assert payload.exp


def test_raise_invalid_token_error_when_token_is_expired(
    monkeypatch,
):
    # arrange
    manager = PyJWTManagerAdapter(key='secret-key')

    def mock_decode(*args, **kwargs):
        raise jwt.exceptions.ExpiredSignatureError('token expired')

    monkeypatch.setattr(jwt, 'decode', mock_decode)

    # act and asserts
    with pytest.raises(InvalidTokenError) as exc:
        manager.validate('expired-token')

    assert exc.value.code == InvalidTokenErrorCode.EXPIRED


def test_raise_invalid_token_error_when_signature_is_invalid(
    monkeypatch,
):
    # arrnge
    manager = PyJWTManagerAdapter(key='secret-key')

    def mock_decode(*args, **kwargs):
        raise jwt.exceptions.InvalidSignatureError('invalid signature')

    monkeypatch.setattr(jwt, 'decode', mock_decode)

    # act and asserts
    with pytest.raises(InvalidTokenError) as exc:
        manager.validate('invalid-token')

    assert exc.value.code == InvalidTokenErrorCode.INVALID_SIGNATURE


@pytest.mark.parametrize(
    'exception',
    [
        jwt.exceptions.DecodeError('decode error'),
        jwt.exceptions.InvalidAlgorithmError('invalid algorithm'),
    ],
)
def test_raise_invalid_token_error_when_token_is_malformed(
    monkeypatch,
    exception,
):
    # arrrange
    manager = PyJWTManagerAdapter(key='secret-key')

    def mock_decode(*args, **kwargs):
        raise exception

    monkeypatch.setattr(jwt, 'decode', mock_decode)

    # act and asserts
    with pytest.raises(InvalidTokenError) as exc:
        manager.validate('malformed-token')

    assert exc.value.code == InvalidTokenErrorCode.MALFORMED


def test_raise_invalid_token_error_when_token_is_invalid(
    monkeypatch,
):
    # arrange
    manager = PyJWTManagerAdapter(key='secret-key')

    def mock_decode(*args, **kwargs):
        raise jwt.exceptions.InvalidTokenError('invalid token')

    monkeypatch.setattr(jwt, 'decode', mock_decode)

    # act and asserts
    with pytest.raises(InvalidTokenError) as exc:
        manager.validate('invalid-token')

    assert exc.value.code == InvalidTokenErrorCode.INVALID


def test_raise_infrastructure_error_when_unexpected_error_occurs(
    monkeypatch,
):
    # arrange
    manager = PyJWTManagerAdapter(key='secret-key')

    original_error = Exception('unexpected failure')

    def mock_decode(*args, **kwargs):
        raise original_error

    monkeypatch.setattr(jwt, 'decode', mock_decode)

    # act and asserts
    with pytest.raises(InfrastructureError) as exc:
        manager.validate('token')

    assert exc.value.code == InfrastructureErrorCode.UNKNOWN
    assert str(exc.value) == 'Unexpected error during token decoding.'
    assert exc.value.cause is original_error
