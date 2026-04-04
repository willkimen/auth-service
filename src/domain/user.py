import uuid
from datetime import datetime, timezone

from domain.exceptions import InvalidTimestampError
from domain.utils import ensure_aware, ensure_not_future
from domain.value_objects import Email, PlainPassword


class User:
    def __init__(
        self,
        public_id: uuid.UUID,
        email: str,
        plain_password: str,
        email_verified: bool,
        is_active: bool,
        created_at: datetime,
        updated_at: datetime,
        last_login_at: datetime | None,
    ):
        self._public_id: uuid.UUID = public_id

        self._email: Email = Email(email)
        self._plain_password: PlainPassword = PlainPassword(plain_password)

        self._email_verified: bool = email_verified
        self._is_active: bool = is_active

        self._created_at: datetime = User._validate_created_at(created_at)
        self._updated_at: datetime = self._validate_updated_at(updated_at)
        self._last_login_at: datetime | None = self._validate_last_login_at(
            last_login_at
        )

    @property
    def plain_password(self) -> PlainPassword:
        return self._plain_password

    def change_password(self, new: str):
        new_password = PlainPassword(new)

        if new_password == self._plain_password:
            return

        self._register_update()

        self._plain_password = new_password

    @property
    def email(self) -> Email:
        return self._email

    def change_email(self, new: str):
        new_email = Email(new)

        if new_email == self._email:
            return

        self._register_update()

        self._email = new_email

    @property
    def is_active(self) -> bool:
        return self._is_active

    def activate(self):
        if self._is_active:
            return

        self._register_update()

        self._is_active = True

    def deactivate(self):
        if not self._is_active:
            return

        self._register_update()

        self._is_active = False

    @property
    def email_verified(self) -> bool:
        return self._email_verified

    def mark_email_as_verified(self):
        if self._email_verified:
            return

        self._register_update()

        self._email_verified = True

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
        now = datetime.now(timezone.utc)
        self._last_login_at = self._validate_last_login_at(now)

    def _validate_not_before_created_at(
        self, date: datetime, field: str
    ) -> datetime:
        if date < self._created_at:
            raise InvalidTimestampError(
                f'{field} must not be before created_at'
            )

        return date

    def _register_update(self):
        now = datetime.now(timezone.utc)
        self._updated_at = self._validate_updated_at(now)

    @staticmethod
    def _validate_created_at(created_at: datetime) -> datetime:
        if created_at is None:
            raise InvalidTimestampError('created_at must not be None')

        ensure_aware(created_at, 'created_at')
        ensure_not_future(created_at, 'created_at')

        return created_at

    def _validate_updated_at(self, updated_at: datetime) -> datetime:
        if updated_at is None:
            raise InvalidTimestampError('updated_at must not be None')

        ensure_aware(updated_at, 'updated_at')
        ensure_not_future(updated_at, 'updated_at')
        self._validate_not_before_created_at(updated_at, 'updated_at')

        return updated_at

    def _validate_last_login_at(
        self, last_login_at: datetime | None
    ) -> datetime | None:
        if last_login_at is None:
            return None

        ensure_aware(last_login_at, 'last_login_at')
        ensure_not_future(last_login_at, 'last_login_at')
        self._validate_not_before_created_at(last_login_at, 'last_login_at')

        return last_login_at
