from __future__ import annotations

import secrets

from domain.exceptions import CodeErrorCode, InvalidCodeError


class Code:
    """Represents a code value object.

    Ensures the code is a 6-digit numeric string.

    Args:
        value (str): Code value.

    Raises:
        InvalidCodeError: If not a 6-digit numeric string.
        TypeError: If value is not a string.
        ValueError: If value is empty.
    """

    _LENGTH = 6

    def __init__(self, value: str):
        self._value = self._validate(value)

    @property
    def value(self) -> str:
        return self._value

    @classmethod
    def generate(cls) -> Code:
        value = ''.join(
            secrets.choice('0123456789') for _ in range(cls._LENGTH)
        )
        return cls(value)

    def _validate(self, value: str) -> str:
        """Validates the code value.

        Args:
            value (str): Code value.

        Returns:
            str: Validated code.

        Raises:
            InvalidCodeError: If code be not 6-digit numeric string.
            TypeError: If code is not a string.
            ValueError: If code is empty.
        """
        if not isinstance(value, str):
            raise TypeError(
                f'Invalid code: expected str, got {type(value).__name__}'
            )

        if not value.strip():
            raise ValueError('code cannot be empty')

        if len(value) != self._LENGTH or not value.isdigit():
            raise InvalidCodeError(
                'code must be a 6-digit numeric string',
                CodeErrorCode.CODE_INVALID_FORMAT,
            )

        return value

    def __hash__(self):
        return hash(self._value)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Code):
            return NotImplemented
        return self._value == other._value
