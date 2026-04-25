from __future__ import annotations

import copy
import uuid
from datetime import datetime

from domain.enums import CodeType
from domain.exceptions import (
    CodeStatusError,
    CodeTypeError,
    InvalidTimestampError,
)
from domain.utils import (
    ensure_aware,
    ensure_not_none,
)
from domain.value_objects.code import Code


class VerificationCode:
    """
    Represents a verification code entity with validation rules.

    Args:
        `code` (Code | None): Code instance or None to auto-generate.
        `user_public_id` (UUID): Owner user identifier.
        `type` (CodeType): Verification code type.
        `created_at` (datetime): Creation timestamp.
        `expires_at` (datetime): Expiration timestamp.
        `used_at` (datetime | None): Usage timestamp.
        `sent_at` (datetime | None): Send timestamp.
        `payload` (dict | None): Optional metadata.

    Raises:
        RequiredFieldError:
            - If `user_public_id` is None.
            - If `code_type` is None.
            - If `created_at` is None.
            - If `expires_at` is None.
        InvalidTimestampError:
            - If `created_at` has no timezone information.
            - If `expires_at` has no timezone information.
            - If `expires_at` is earlier than `created_at`.
            - If `used_at` has no timezone information.
            - If `used_at` is earlier than `created_at`.
            - If `sent_at` has no timezone information.
            - If `sent_at` is earlier than `created_at`.
        CodeTypeError:
            - If `code_type` is not CodeType type.
        TypeError:
            - If `user_public_id` is not UUID type.
    """

    def __init__(
        self,
        code: Code | None,
        user_public_id: uuid.UUID,
        type: CodeType,
        created_at: datetime,
        expires_at: datetime,
        used_at: datetime | None = None,
        sent_at: datetime | None = None,
        payload: dict | None = None,
    ):
        self._code = code or Code.generate()

        self._user_public_id: uuid.UUID = (
            VerificationCode._validate_user_public_id(user_public_id)
        )

        self._type: CodeType = VerificationCode._validate_type(type)

        self._created_at: datetime = VerificationCode._validate_created_at(
            created_at
        )
        self._expires_at: datetime = self._validate_expires_at(expires_at)
        self._used_at: datetime | None = self._validate_used_at(used_at)
        self._sent_at: datetime | None = self._validate_sent_at(sent_at)

        self._payload: dict | None = payload

    def __hash__(self):
        return hash(self.code)

    def __eq__(self, other) -> bool:
        if not isinstance(other, VerificationCode):
            return NotImplemented
        return self.code == other.code

    @property
    def code(self) -> Code:
        return self._code

    @property
    def user_public_id(self) -> uuid.UUID:
        return self._user_public_id

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

    def has_been_sent(self) -> bool:
        """Checks if the code has been sent.

        Returns:
            bool: True if sent.
        """
        return self._sent_at is not None

    def mark_as_used(self, used_at: datetime):
        """Marks the code as used.

        Args:
            used_at (datetime): Usage timestamp.

        Raises:
            InvalidTimestampError: If not aware or before created_at.
            CodeStatusError: If the code is not active.
        """
        if self.is_used():
            return

        self._validate_used_at(used_at)

        if self.is_expired(used_at):
            raise CodeStatusError('code cannot be used because is has expired')

        self._used_at = used_at

    def mark_as_sent(self, sent_at: datetime):
        """Marks the code as sent.

        Args:
            sent_at (datetime): Sent timestamp.

        Raises:
            InvalidTimestampError: If not aware or before created_at.
        """
        self._validate_sent_at(sent_at)
        self._sent_at = sent_at

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
    def _validate_user_public_id(user_public_id: uuid.UUID) -> uuid.UUID:
        """Validates the user id.

        Args:
            user_public_id (UUID): User identifier.

        Returns:
            int: Validated user_public_id.

        Raises:
            RequiredFieldError: If user_public_id is None.
            TypeError: If user_public_id is not an uuid type.
        """
        ensure_not_none(user_public_id, 'user_public_id')

        if not isinstance(user_public_id, uuid.UUID):
            raise TypeError(
                f'Invalid user_public_id: expected uuid type, '
                f'got {type(user_public_id).__name__}'
            )

        return user_public_id

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
    def _validate_created_at(created_at: datetime) -> datetime:
        """Validates created_at timestamp.

        Args:
            created_at (datetime): Creation timestamp.

        Returns:
            datetime: Validated timestamp.

        Raises:
            RequiredFieldError: If None.
            InvalidTimestampError: If not aware.
        """
        ensure_not_none(created_at, 'created_at')
        ensure_aware(created_at, 'created_at')

        return created_at

    def _validate_expires_at(self, expires_at: datetime) -> datetime:
        """Validates expires_at timestamp.

        Args:
            expires_at (datetime): Expiration timestamp.

        Returns:
            datetime: Validated timestamp.

        Raises:
            RequiredFieldError: If None.
            InvalidTimestampError: If not aware or before created_at.
        """
        ensure_not_none(expires_at, 'expires_at')
        ensure_aware(expires_at, 'expires_at')
        self._validate_not_before_created_at(expires_at, 'expires_at')

        return expires_at

    def _validate_used_at(self, used_at: datetime | None) -> datetime | None:
        """Validates used_at timestamp.

        Args:
            used_at (datetime | None): Usage timestamp.

        Returns:
            datetime | None: Validated timestamp.

        Raises:
            InvalidTimestampError: If not aware or before created_at.
        """
        if used_at is None:
            return None

        ensure_aware(used_at, 'used_at')
        self._validate_not_before_created_at(used_at, 'used_at')

        return used_at

    def _validate_sent_at(self, sent_at: datetime | None) -> datetime | None:
        """Validates sent_at timestamp.

        Args:
            sent_at (datetime | None): Sent timestamp.

        Returns:
            datetime | None: Validated timestamp.

        Raises:
            InvalidTimestampError: If not aware or before created_at.
        """
        if sent_at is None:
            return None

        ensure_aware(sent_at, 'sent_at')
        self._validate_not_before_created_at(sent_at, 'sent_at')

        return sent_at
