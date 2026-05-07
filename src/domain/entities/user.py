from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from domain.utils import ensure_aware, ensure_not_none
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


class User:
    """
    Represents a user entity with validation and domain rules.

    Args:
        `public_id` (UUID): Public user identifier.
        `email` (Email): Email instance.
        `hash_password` (PasswordHash): PasswordHash instance.
        `email_verified` (bool): Email verification status.
        `is_active` (bool): Active status.
        `created_at` (datetime): Creation timestamp.
        `updated_at` (datetime): Update timestamp.
        `last_login_at` (datetime | None): Last login timestamp.

    Raises:
        ValueError:
            - If `public_id` is None.
            - If `email_verified` is None.
            - If `is_active` is None.
            - If `created_at` is None.
            - If `updated_at` is None.
            - If `created_at` has no timezone information.
            - If `updated_at` has no timezone information.
            - If `updated_at` is earlier than `created_at`.
            - If `last_login_at` has no timezone information.
            - If `last_login_at` is earlier than `created_at`.
        TypeError:
            - If `public_id` is not UUID type.
            - If `email_verified` is not bool type.
            - If `is_active` is not bool type.
    """

    def __init__(
        self,
        public_id: uuid.UUID,
        email: Email,
        hash_password: PasswordHash,
        email_verified: bool,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
        last_login_at: datetime | None,
    ):
        self._public_id: uuid.UUID = User._validate_public_id(public_id)

        self._email: Email = email
        self._hash_password: PasswordHash = hash_password

        self._email_verified: bool = User._validate_email_verified(
            email_verified
        )
        self._is_active: bool = User._validate_is_active(is_active)

        self._created_at: datetime = User._validate_created_at(created_at)
        self._updated_at: datetime = self._validate_updated_at(updated_at)
        self._last_login_at: datetime | None = self._validate_last_login_at(
            last_login_at
        )

    @property
    def hash_password(self) -> PasswordHash:
        return self._hash_password

    def change_password(self, new: PasswordHash):
        """Changes the user's password hash and updates updated_at.

        Args:
            new (PasswordHash): PasswordHash instance.
        """
        if new == self._hash_password:
            return

        self._register_update()

        self._hash_password = new

    @property
    def email(self) -> Email:
        return self._email

    def change_email(self, new: Email):
        """Changes the user's email and updates updated_at.

        Args:
            new (Email): Email instance.
        """
        if new == self._email:
            return

        self._register_update()

        self._email = new

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self):
        """Activates the user and updates updated_at.

        Does nothing if already active.
        """
        if self._is_active:
            return

        self._register_update()

        self._is_active = True

    def deactivate(self):
        """Deactivates the user and updates updated_at.

        Does nothing if already inactive.
        """
        if not self._is_active:
            return

        self._register_update()

        self._is_active = False

    @property
    def email_verified(self) -> bool:
        return self._email_verified

    def mark_email_as_verified(self):
        """Marks the email as verified and updates updated_at.

        Does nothing if already verified.
        """
        if self._email_verified:
            return

        self._register_update()

        self._email_verified = True

    def should_be_deleted(self, now: datetime, deadline: timedelta) -> bool:
        """Checks if the user should be deleted.

        User must be unverified and past the deadline since created_at.

        Args:
            now (datetime): Current timestamp.
            deadline (timedelta): Allowed time window.

        Returns:
            bool: True if should be deleted.
        """
        if self.email_verified:
            return False

        return now > self.created_at + deadline

    @property
    def public_id(self) -> uuid.UUID:
        return self._public_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def last_login_at(self) -> datetime | None:
        return self._last_login_at

    def record_login(self):
        """Records a login and updates last_login_at.

        Uses current UTC time. Timestamp must be timezone-aware
        and not before created_at.

        Raises:
            ValueError: If timestamp is invalid or before
            created_at.
        """
        now = datetime.now(timezone.utc)
        self._last_login_at = self._validate_last_login_at(now)

    def __hash__(self):
        return hash(self.public_id)

    def __eq__(self, other) -> bool:
        if not isinstance(other, User):
            return NotImplemented
        return self.public_id == other.public_id

    def _validate_not_before_created_at(
        self, date: datetime, field: str
    ) -> datetime:
        """Ensures a timestamp is not before created_at.

        Args:
            date (datetime): Timestamp to validate.
            field (str): Field name.

        Returns:
            datetime: Validated timestamp.

        Raises:
            ValueError: If date is before created_at.
        """
        if date < self._created_at:
            raise ValueError(f'{field} must not be before created_at')

        return date

    def _register_update(self):
        """Updates updated_at with current UTC time.

        Validates timestamp as timezone-aware and not before created_at.

        Raises:
            ValueError: If timestamp is invalid or before
            created_at.
        """
        now = datetime.now(timezone.utc)
        self._updated_at = self._validate_updated_at(now)

    @staticmethod
    def _validate_created_at(created_at: datetime) -> datetime:
        """Validates created_at timestamp.

        Ensures value is not None and is timezone-aware.

        Args:
            created_at (datetime): Creation timestamp.

        Returns:
            datetime: Validated timestamp.

        Raises:
            ValueError: If None or not aware.
        """
        ensure_not_none(created_at, 'created_at')
        ensure_aware(created_at, 'created_at')

        return created_at

    def _validate_updated_at(self, updated_at: datetime) -> datetime:
        """Validates updated_at timestamp.

        Ensures value is not None, is timezone-aware and
        and not before created_at.

        Args:
            updated_at (datetime): Update timestamp.

        Returns:
            datetime: Validated timestamp.

        Raises:
            ValueError: If None, not aware or before created_at.
        """
        ensure_not_none(updated_at, 'updated_at')
        ensure_aware(updated_at, 'updated_at')
        self._validate_not_before_created_at(updated_at, 'updated_at')

        return updated_at

    def _validate_last_login_at(
        self, last_login_at: datetime | None
    ) -> datetime | None:
        """Validates last_login_at timestamp.

        Allows None. If provided, must be timezone-aware and
        not before created_at.

        Args:
            last_login_at (datetime | None): Login timestamp.

        Returns:
            datetime | None: Validated timestamp.

        Raises:
            ValueError: If not aware or before created_at.
        """
        if last_login_at is None:
            return None

        ensure_aware(last_login_at, 'last_login_at')
        self._validate_not_before_created_at(last_login_at, 'last_login_at')

        return last_login_at

    @staticmethod
    def _validate_public_id(public_id: uuid.UUID) -> uuid.UUID:
        """Validates public_id.

        Ensures value is not None and is a UUID.

        Args:
            public_id (UUID): Public identifier.

        Returns:
            UUID: Validated identifier.

        Raises:
            ValueError: If None.
            TypeError: If not a UUID.
        """
        ensure_not_none(public_id, 'public_id')

        if not isinstance(public_id, uuid.UUID):
            raise TypeError(
                f'Invalid id: expected UUID, got {type(public_id).__name__}'
            )

        return public_id

    @staticmethod
    def _validate_email_verified(email_verified: bool) -> bool:
        """Validates email_verified flag.

        Ensures value is not None and is a boolean.

        Args:
            email_verified (bool): Verification status.

        Returns:
            bool: Validated value.

        Raises:
            ValueError: If None.
            TypeError: If not a bool.
        """
        ensure_not_none(email_verified, 'email_verified')

        if not isinstance(email_verified, bool):
            raise TypeError(
                f'Invalid email_verified: expected bool, '
                f'got {type(email_verified).__name__}'
            )

        return email_verified

    @staticmethod
    def _validate_is_active(is_active: bool) -> bool:
        """Validates is_active flag.

        Ensures value is not None and is a boolean.

        Args:
            is_active (bool): Active status.

        Returns:
            bool: Validated value.

        Raises:
            ValueError: If None.
            TypeError: If not a bool.
        """
        ensure_not_none(is_active, 'is_active')

        if not isinstance(is_active, bool):
            raise TypeError(
                f'Invalid is_active: expected bool, '
                f'got {type(is_active).__name__}'
            )

        return is_active
