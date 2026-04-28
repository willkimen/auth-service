from domain.exceptions import InvalidPasswordError, PasswordErrorCode


class PasswordHash:
    """Represents a password hash value object with validation.

    Ensures the hash is non-empty and compared by value.

    Args:
        value (bytes): Password hash bytes.

    Raises:
        InvalidPasswordError: If the hash is empty.
    """

    def __init__(self, value: bytes):
        self._value = PasswordHash._validate(value)

    @property
    def value(self) -> bytes:
        return self._value

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PasswordHash):
            return NotImplemented
        return self._value == other._value

    @staticmethod
    def _validate(value: bytes) -> bytes:
        if not value:
            raise InvalidPasswordError(
                'password hash cannot be empty', PasswordErrorCode.REQUIRED
            )

        return value
