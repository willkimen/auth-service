from datetime import datetime

from domain.exceptions import InvalidTimestampError, RequiredFieldError


def ensure_aware(dt: datetime, field: str):
    """Ensures a datetime is timezone-aware.

    Args:
        dt (datetime): Datetime to validate.
        field (str): Field name.

    Raises:
        InvalidTimestampError: If dt is not timezone-aware.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise InvalidTimestampError(f'{field} must be timezone-aware')


def ensure_not_none(value, field: str):
    """Ensures a value is not None.

    Args:
        value: Value to validate.
        field (str): Field name.

    Raises:
        RequiredFieldError: If value is None.
    """
    if value is None:
        raise RequiredFieldError(f'{field} it is required')
