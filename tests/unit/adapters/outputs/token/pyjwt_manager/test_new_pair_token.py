import uuid

import pytest

from adapters.outputs.token.pyjwt_manager import PyJWTManagerAdapter
from application.dtos.token_dto import PairTokensDTO
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)

sub = uuid.uuid4()


def test_return_valid_access_and_refresh_tokens():
    # arrange
    manager = PyJWTManagerAdapter(key='secret-key')

    # act
    pair = manager.new_pair_token(sub)

    # asserts
    assert isinstance(pair, PairTokensDTO)

    assert pair.access is not None
    assert pair.refresh is not None

    assert isinstance(pair.access.token, str)
    assert isinstance(pair.refresh.token, str)

    assert pair.access.token != pair.refresh.token

    access_payload = pair.access.payload
    refresh_payload = pair.refresh.payload

    assert access_payload.sub == str(sub)
    assert refresh_payload.sub == str(sub)

    assert access_payload.typ == 'access'
    assert refresh_payload.typ == 'refresh'

    assert access_payload.jti
    assert refresh_payload.jti

    assert access_payload.exp
    assert refresh_payload.exp


def test_raise_infrastructure_error_when_payload_creation_fails(
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
        manager.new_pair_token(sub)

    assert exc.value.code == InfrastructureErrorCode.AUTH_TOKEN
    assert exc.value.cause is original_error


def test_raise_infrastructure_error_when_token_creation_fails(
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
        manager.new_pair_token(sub)

    assert exc.value.code == InfrastructureErrorCode.AUTH_TOKEN
    assert exc.value.cause is original_error
