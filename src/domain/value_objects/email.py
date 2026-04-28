import re

from domain.exceptions import EmailErrorCode, InvalidEmailError

_EMAIL_PATTERN = re.compile(r'^[\w\.\+-]+@[\w\.-]+\.\w+$')


class Email:
    """Represents an email value object with validation.

    Ensures the email is valid, normalized, and compared by value.

    Args:
        value (str): Raw email string.

    Raises:
        InvalidEmailError: If email is None, empty, or invalid.
    """

    def __init__(self, value: str):
        self._value: str = Email._validate(value)

    @property
    def value(self) -> str:
        return self._value

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return NotImplemented
        return self._value == other._value

    @staticmethod
    def _validate(value: str) -> str:
        if value is None or not value.strip():
            raise InvalidEmailError(
                'email cannot be None or empty', EmailErrorCode.REQUIRED
            )

        value = value.strip().lower()

        if _EMAIL_PATTERN.match(value) is None:
            raise InvalidEmailError(
                'email must be in a valid format',
                EmailErrorCode.INVALID_FORMAT,
            )

        return value
