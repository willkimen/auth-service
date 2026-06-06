import uuid

import pytest

from adapters.outputs.token.pyjwt_manager import PyJWTManagerAdapter
from application.exceptions import InvalidTokenError, InvalidTokenErrorCode

sub = uuid.uuid4()
TEST_SECRET_KEY = 'super-secret-test-key-with-at-least-32-bytes'
ANOTHER_TEST_SECRET_KEY = 'another-super-secret-test-key-32bytes'


def test_should_validate_generated_access_token():
    """
    Validates the complete access token flow by generating a real token
    through the public API and decoding it afterward.

    The goal is to ensure that:
    - the token can be successfully validated
    - the payload remains consistent end-to-end
    - the generated token preserves all expected claims

    This acts as an integration test between token creation and validation.
    """

    # arrange
    manager = PyJWTManagerAdapter(key=TEST_SECRET_KEY)

    token = manager.new_access(sub)

    # act
    payload = manager.validate(token)

    # asserts
    assert payload.sub == str(sub)
    assert payload.typ == 'access'

    assert payload.jti
    assert payload.exp


def test_should_validate_generated_access_and_refresh_tokens():
    """
    Validates the complete token pair flow by generating both access
    and refresh tokens and validating them afterward.

    The goal is to ensure that:
    - both tokens are valid
    - each token preserves the correct payload data
    - token types are correctly assigned
    - expiration times differ according to token purpose

    This acts as an integration test covering the full lifecycle
    of access and refresh token generation and validation.
    """

    # arrange
    manager = PyJWTManagerAdapter(key=TEST_SECRET_KEY)

    pair = manager.new_pair_token(sub)

    # act
    access_payload = manager.validate(pair.access.token)
    refresh_payload = manager.validate(pair.refresh.token)

    # asserts
    assert access_payload.sub == str(sub)
    assert refresh_payload.sub == str(sub)

    assert access_payload.typ == 'access'
    assert refresh_payload.typ == 'refresh'

    assert access_payload.jti
    assert refresh_payload.jti

    assert access_payload.exp
    assert refresh_payload.exp

    assert access_payload.exp < refresh_payload.exp


def test_should_reject_token_signed_with_different_key():
    """
    Validates that tokens signed with a different secret key
    are rejected during validation.

    The goal is to ensure that token signature verification
    is correctly enforced and that tokens generated outside
    the trusted signing context cannot be accepted.

    This test also validates the integration between JWT signing
    and signature verification mechanisms.
    """

    # arrange
    manager = PyJWTManagerAdapter(key=TEST_SECRET_KEY)
    another_manager = PyJWTManagerAdapter(key=ANOTHER_TEST_SECRET_KEY)

    token = another_manager.new_access(sub)

    # act and asserts
    with pytest.raises(InvalidTokenError) as exc:
        manager.validate(token)

    assert exc.value.code == InvalidTokenErrorCode.TOKEN_INVALID_SIGNATURE


def test_should_reject_manually_modified_token():
    """
    Validates that manually modified tokens are rejected
    during validation.

    The goal is to ensure that token integrity protection
    through cryptographic signature verification is working
    correctly and that any tampering invalidates the token.

    This test simulates a real-world token manipulation attempt.
    """

    # arrange
    manager = PyJWTManagerAdapter(key=TEST_SECRET_KEY)

    token = manager.new_access(sub)

    modified_token = token[:-1] + 'x'

    # act and assert
    with pytest.raises(InvalidTokenError):
        manager.validate(modified_token)


def test_should_reject_empty_token():
    """
    Validates that empty tokens are rejected during validation.

    The goal is to ensure that invalid or incomplete token inputs
    cannot bypass the validation process and are treated as invalid
    authentication artifacts.

    The exact error code may vary depending on PyJWT internal behavior.
    """

    # arrange
    manager = PyJWTManagerAdapter(key=TEST_SECRET_KEY)

    # act and assert
    with pytest.raises(InvalidTokenError) as exc:
        manager.validate('')

    assert exc.value.code in {
        InvalidTokenErrorCode.TOKEN_MALFORMED,
        InvalidTokenErrorCode.TOKEN_INVALID,
    }


def test_should_reject_completely_invalid_token():
    """
    Validates that completely malformed tokens are rejected
    during validation.

    The goal is to ensure that arbitrary or non-JWT inputs
    cannot be interpreted as valid authentication tokens.

    This test simulates scenarios where corrupted, truncated,
    or non-token values are provided to the validation layer.

    The exact error code may vary depending on PyJWT internal behavior.
    """

    # arrange
    manager = PyJWTManagerAdapter(key=TEST_SECRET_KEY)

    # act and assert
    with pytest.raises(InvalidTokenError) as exc:
        manager.validate('abc')

    assert exc.value.code in {
        InvalidTokenErrorCode.TOKEN_MALFORMED,
        InvalidTokenErrorCode.TOKEN_INVALID,
    }
