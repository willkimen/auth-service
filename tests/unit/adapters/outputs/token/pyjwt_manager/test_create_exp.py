from datetime import datetime, timedelta, timezone

from adapters.outputs.token.pyjwt_manager import PyJWTManagerAdapter

# Fixed to resolve PyJWT's InsecureKeyLengthWarning (RFC 7518 compliance).
# Ensures the HMAC key is at least 32 bytes long to satisfy
# security linters and standards.
key = 'a_much_longer_secret_key_with_more_than_32_characters'


def test_should_return_access_expiration_timestamp():
    # arrange
    manager = PyJWTManagerAdapter(key)

    now = datetime.now(timezone.utc)
    expected = int((now + timedelta(minutes=15)).timestamp())

    # act
    exp = manager._create_exp('access')

    # asserts
    assert isinstance(exp, int)

    difference_in_seconds = abs(exp - expected)
    allowed_time_difference_in_seconds = 5
    assert difference_in_seconds < allowed_time_difference_in_seconds


def test_should_return_refresh_expiration_timestamp():
    # arrange
    manager = PyJWTManagerAdapter(key)

    now = datetime.now(timezone.utc)
    expected = int((now + timedelta(days=7)).timestamp())

    # act
    exp = manager._create_exp('refresh')

    # asserts
    assert isinstance(exp, int)

    difference_in_seconds = abs(exp - expected)
    allowed_time_difference_in_seconds = 5
    assert difference_in_seconds < allowed_time_difference_in_seconds
