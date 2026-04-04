from datetime import datetime, timezone

from domain.exceptions import InvalidTimestampError


def ensure_not_future(date: datetime, field: str):
    now = datetime.now(timezone.utc)
    if date > now:
        raise InvalidTimestampError(f'{field} must not be in the future')


def ensure_not_past(date: datetime, field: str):
    now = datetime.now(timezone.utc)
    if date < now:
        raise InvalidTimestampError(f'{field} must not be in the past')


def ensure_aware(dt: datetime, field: str):
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise InvalidTimestampError(f'{field} must be timezone-aware')
