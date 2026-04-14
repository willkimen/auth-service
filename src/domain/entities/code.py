from __future__ import annotations

import copy
import secrets
from datetime import datetime

from domain.enums import CodeType
from domain.exceptions import (
    CodeStatusError,
    CodeTypeError,
    InvalidTimestampError,
)
from domain.utils import (
    ensure_aware,
    ensure_not_future,
    ensure_not_none,
)


class VerificationCode:
    """Represents a verification code entity with validation rules.

    Handles lifecycle, status, and validation of verification codes.

    Timestamps must be timezone-aware. created_at must not be in the
    future. expires_at and used_at must not be before created_at.

    Args:
        code (str | None): Code value or None to auto-generate.
        user_id (int): Owner user identifier.
        type (CodeType): Verification code type.
        created_at (datetime): Creation timestamp.
        expires_at (datetime): Expiration timestamp.
        used_at (datetime | None): Usage timestamp.
        payload (dict | None): Optional metadata.

    Raises:
        RequiredFieldError: If required fields are None.
        InvalidTimestampError: If timestamps are invalid or inconsistent.
        CodeTypeError: If type is not a valid CodeType.
        CodeStatusError: If marking as used when not active.
        TypeError: If code or user_id have invalid types.
        ValueError: If code is empty.
    """

    def __init__(
        self,
        code: str | None,
        user_id: int,
        type: CodeType,
        created_at: datetime,
        expires_at: datetime,
        used_at: datetime | None = None,
        payload: dict | None = None,
    ):
        if code is None:
            self._code: str = VerificationCode._generate_code()
        else:
            self._code: str = VerificationCode._validate_code(code)

        self._user_id: int = VerificationCode._validate_user_id(user_id)

        self._type: CodeType = VerificationCode._validate_type(type)

        self._created_at: datetime = VerificationCode._validate_created_at(
            created_at
        )
        self._expires_at: datetime = self._validate_expires_at(expires_at)
        self._used_at: datetime | None = self._validate_used_at(used_at)

        self._payload: dict | None = payload

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other) -> bool:
        if not isinstance(other, VerificationCode):
            return NotImplemented
        return self.code == other.code

    @property
    def code(self) -> str:
        return self._code

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def type(self) -> CodeType:
        return self._type

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def used_at(self) -> datetime | None:
        return self._used_at

    @property
    def payload(self) -> dict | None:
        return copy.copy(self._payload)

    def has_new_email(self) -> bool:
        """Verifica se o payload contém um novo email.

        Returns:
            bool: True se houver 'new_email' no payload.
        """
        if self._payload is not None:
            return self._payload.get('new_email') is not None

        return False

    def is_active(self, now: datetime) -> bool:
        """Checks if the code is active.

        Args:
            now (datetime): Current timestamp.

        Returns:
            bool: True if active.

        Raises:
            InvalidTimestampError: If now is not timezone-aware.
        """
        return not self.is_used() and not self.is_expired(now)

    def is_used(self) -> bool:
        """Checks if the code has been used.

        Returns:
            bool: True if used.
        """
        return self._used_at is not None

    def is_expired(self, now: datetime) -> bool:
        """Checks if the code is expired.

        Args:
            now (datetime): Current timestamp.

        Returns:
            bool: True if expired.

        Raises:
            InvalidTimestampError: If now is not timezone-aware.
        """
        ensure_aware(now, 'now')

        return now >= self._expires_at

    def mark_as_used(self, now: datetime):
        """Marks the code as used.

        Args:
            now (datetime): Usage timestamp.

        Raises:
            InvalidTimestampError: If now is not timezone-aware.
            CodeStatusError: If the code is not active.
        """
        ensure_aware(now, 'now')

        if not self.is_active(now):
            raise CodeStatusError('code cannot be used')
        self._used_at = now

    # private methods
    @staticmethod
    def _generate_code() -> str:
        return ''.join(secrets.choice('0123456789') for _ in range(6))

    def _validate_not_before_created_at(
        self, at: datetime, field: str
    ) -> datetime:
        """Ensures a timestamp is not before created_at.

        Args:
            at (datetime): Timestamp to validate.
            field (str): Field name.

        Returns:
            datetime: Validated timestamp.

        Raises:
            InvalidTimestampError: If before created_at.
        """
        if at < self._created_at:
            raise InvalidTimestampError(
                f'{field} must not be before created_at'
            )

        return at

    @staticmethod
    def _validate_code(code: str) -> str:
        """Validates the code value.

        Args:
            code (str): Code value.

        Returns:
            str: Validated code.

        Raises:
            TypeError: If code is not a string.
            ValueError: If code is empty.
        """
        if not isinstance(code, str):
            raise TypeError(
                f'Invalid code: expected str, got {type(code).__name__}'
            )

        if not code.strip():
            raise ValueError('code cannot be empty')

        return code

    @staticmethod
    def _validate_user_id(id: int) -> int:
        """Validates the user id.

        Args:
            id (int): User identifier.

        Returns:
            int: Validated id.

        Raises:
            RequiredFieldError: If id is None.
            TypeError: If id is not an int.
        """
        ensure_not_none(id, 'user_id')

        if type(id) is not int:
            raise TypeError(
                f'Invalid id: expected int, got {type(id).__name__}'
            )

        return id

    @staticmethod
    def _validate_type(code_type: CodeType) -> CodeType:
        """Validates the code type.

        Args:
            code_type (CodeType): Code type.

        Returns:
            CodeType: Validated type.

        Raises:
            RequiredFieldError: If type is None.
            CodeTypeError: If not a valid CodeType.
        """
        ensure_not_none(code_type, 'type')

        if not isinstance(code_type, CodeType):
            raise CodeTypeError(
                f'Invalid code type: expected CodeType, '
                f'got {type(code_type).__name__}'
            )

        return code_type

    @staticmethod
    def _validate_created_at(at: datetime) -> datetime:
        """Validates created_at timestamp.

        Args:
            at (datetime): Creation timestamp.

        Returns:
            datetime: Validated timestamp.

        Raises:
            RequiredFieldError: If None.
            InvalidTimestampError: If not aware or in future.
        """
        ensure_not_none(at, 'created_at')
        ensure_aware(at, 'created_at')
        ensure_not_future(at, 'created_at')

        return at

    def _validate_expires_at(self, at: datetime) -> datetime:
        """Validates expires_at timestamp.

        Args:
            at (datetime): Expiration timestamp.

        Returns:
            datetime: Validated timestamp.

        Raises:
            RequiredFieldError: If None.
            InvalidTimestampError: If not aware or before created_at.
        """
        ensure_not_none(at, 'expires_at')
        ensure_aware(at, 'expires_at')
        self._validate_not_before_created_at(at, 'expires_at')

        return at

    def _validate_used_at(self, at: datetime | None) -> datetime | None:
        """Validates used_at timestamp.

        Args:
            at (datetime | None): Usage timestamp.

        Returns:
            datetime | None: Validated timestamp.

        Raises:
            InvalidTimestampError: If not aware or before created_at.
        """
        if at is None:
            return None

        ensure_aware(at, 'used_at')
        self._validate_not_before_created_at(at, 'used_at')

        return at
