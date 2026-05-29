import uuid

import pytest

from adapters.outputs.token.pyjwt_manager import PyJWTManagerAdapter
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)

sub = uuid.uuid4()


def test_return_valid_access_token():
    # arrange
    manager = PyJWTManagerAdapter(key='secret-key')

    # act
    token = manager.new_access(sub)

    # asserts
    assert isinstance(token, str)

    payload = manager.validate(token)

    assert payload.sub == str(sub)
    assert payload.typ == 'access'

    assert payload.jti
    assert payload.exp


def test_raise_infrastructure_error_when_access_payload_creation_fails(
    monkeypatch,
):
    # arrange
    manager = PyJWTManagerAdapter(key='secret-key')

    original_error = RuntimeError('payload creation failed')

    def mock_create_payload(*args, **kwargs):
        raise original_error

    monkeypatch.setattr(
        manager,
        '_create_payload',
        mock_create_payload,
    )

    # act and asserts
    with pytest.raises(InfrastructureError) as exc:
        manager.new_access(sub)

    assert exc.value.code == InfrastructureErrorCode.AUTH_TOKEN
    assert exc.value.cause is original_error


def test_raise_infrastructure_error_when_access_token_creation_fails(
    monkeypatch,
):
    # arrange
    manager = PyJWTManagerAdapter(key='secret-key')

    original_error = RuntimeError('token creation failed')

    def mock_create_token(*args, **kwargs):
        raise original_error

    monkeypatch.setattr(
        manager,
        '_create_token',
        mock_create_token,
    )

    # act and asserts
    with pytest.raises(InfrastructureError) as exc:
        manager.new_access(sub)

    assert exc.value.code == InfrastructureErrorCode.AUTH_TOKEN
    assert exc.value.cause is original_error
