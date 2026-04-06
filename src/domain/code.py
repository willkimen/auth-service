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
        if self._payload is not None:
            return self._payload.get('new_email') is not None

        return False

    def is_active(self, now: datetime) -> bool:
        return not self.is_used() and not self.is_expired(now)

    def is_used(self) -> bool:
        return self._used_at is not None

    def is_expired(self, now: datetime) -> bool:
        ensure_aware(now, 'now')

        return now >= self._expires_at

    def mark_as_used(self, now: datetime):
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
        if at < self._created_at:
            raise InvalidTimestampError(
                f'{field} must not be before created_at'
            )

        return at

    @staticmethod
    def _validate_code(code: str) -> str:
        if not isinstance(code, str):
            raise TypeError(
                f'Invalid code: expected str, got {type(code).__name__}'
            )

        if not code.strip():
            raise ValueError('code cannot be empty')

        return code

    @staticmethod
    def _validate_user_id(id: int) -> int:
        ensure_not_none(id, 'user_id')

        if type(id) is not int:
            raise TypeError(
                f'Invalid id: expected int, got {type(id).__name__}'
            )

        return id

    @staticmethod
    def _validate_type(code_type: CodeType) -> CodeType:
        ensure_not_none(code_type, 'type')

        if not isinstance(code_type, CodeType):
            raise CodeTypeError(
                f'Invalid code type: expected CodeType, '
                f'got {type(code_type).__name__}'
            )

        return code_type

    @staticmethod
    def _validate_created_at(at: datetime) -> datetime:
        ensure_not_none(at, 'created_at')
        ensure_aware(at, 'created_at')
        ensure_not_future(at, 'created_at')

        return at

    def _validate_expires_at(self, at: datetime) -> datetime:
        ensure_not_none(at, 'expires_at')
        ensure_aware(at, 'expires_at')
        self._validate_not_before_created_at(at, 'expires_at')

        return at

    def _validate_used_at(self, at: datetime | None) -> datetime | None:
        if at is None:
            return None

        ensure_aware(at, 'used_at')
        self._validate_not_before_created_at(at, 'used_at')

        return at
