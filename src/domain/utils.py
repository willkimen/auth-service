from datetime import datetime, timezone

from domain.exceptions import InvalidTimestampError, RequiredFieldError


def ensure_not_future(date: datetime, field: str):
    now = datetime.now(timezone.utc)
    if date > now:
        raise InvalidTimestampError(f'{field} must not be in the future')


def ensure_aware(dt: datetime, field: str):
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise InvalidTimestampError(f'{field} must be timezone-aware')


def ensure_not_none(value, field_name: str):
    if value is None:
        raise RequiredFieldError(f'{field_name} it is required')
