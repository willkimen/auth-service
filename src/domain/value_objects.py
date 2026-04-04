import re

from domain.exceptions import (
    InvalidEmailError,
    InvalidPasswordError,
)

_EMAIL_PATTERN = re.compile(r'^[\w\.\+-]+@[\w\.-]+\.\w+$')


class Email:
    def __init__(self, value: str):
        self._value: str = Email._validate(value)

    @property
    def value(self) -> str:
        return self._value

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return False
        return self._value == other._value

    @staticmethod
    def _validate(value: str) -> str:
        if value is None or not value.strip():
            raise InvalidEmailError('email cannot be None or empty')

        value = value.strip().lower()

        if _EMAIL_PATTERN.match(value) is None:
            raise InvalidEmailError('email must be in a valid format')

        return value


_min_length_password = 8
_max_length_password = 128


class PlainPassword:
    def __init__(self, value: str):
        self._value = PlainPassword._validate(value)

    @property
    def value(self) -> str:
        return self._value

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PlainPassword):
            return False
        return self._value == other._value

    @staticmethod
    def _validate(value: str) -> str:
        if value is None or not value.strip():
            raise InvalidPasswordError('password cannot be empty')

        if len(value) < _min_length_password:
            raise InvalidPasswordError('password too short')

        if len(value) > _max_length_password:
            raise InvalidPasswordError('password too long')

        if not any(c.isalpha() for c in value):
            raise InvalidPasswordError(
                'password must contain at least one letter'
            )

        if not any(c.isdigit() for c in value):
            raise InvalidPasswordError(
                'password must contain at least one number'
            )

        if not any(not c.isalnum() for c in value):
            raise InvalidPasswordError(
                'password must contain at least one special character'
            )

        if not any(c.isupper() for c in value):
            raise InvalidPasswordError(
                'password must contain at least one uppercase character'
            )

        if not any(c.islower() for c in value):
            raise InvalidPasswordError(
                'password must contain at least one lowercase character'
            )

        return value


class PasswordHash:
    def __init__(self, value: bytes):
        self._value = PasswordHash._validate(value)

    @property
    def value(self) -> bytes:
        return self._value

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PasswordHash):
            return False
        return self._value == other._value

    @staticmethod
    def _validate(value: bytes) -> bytes:
        if not value:
            raise InvalidPasswordError('password hash cannot be empty')

        return value
