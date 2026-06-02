import uuid

from adapters.outputs.token.pyjwt_manager import PyJWTManagerAdapter

sub = uuid.uuid4()
# Fixed to resolve PyJWT's InsecureKeyLengthWarning (RFC 7518 compliance).
# Ensures the HMAC key is at least 32 bytes long to satisfy
# security linters and standards.
key = 'a_much_longer_secret_key_with_more_than_32_characters'


def test_create_payload_with_expected_structure_and_values():
    # arrange
    manager = PyJWTManagerAdapter(key)

    # act
    payload = manager._create_payload(sub, 'access')

    # asserts
    assert 'jti' in payload
    assert 'sub' in payload
    assert 'exp' in payload
    assert 'typ' in payload

    assert payload['sub'] == str(sub)
    assert payload['typ'] == 'access'

    assert isinstance(payload['exp'], int)

    assert isinstance(payload['jti'], str)


def test_should_generate_different_jti_for_each_payload():
    # arrange
    manager = PyJWTManagerAdapter(key)

    # act
    first_payload = manager._create_payload(sub, 'access')
    second_payload = manager._create_payload(sub, 'access')

    # assert
    assert first_payload['jti'] != second_payload['jti']
