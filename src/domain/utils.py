from datetime import datetime


def ensure_aware(dt: datetime, field: str):
    """Ensures a datetime is timezone-aware.

    Args:
        dt (datetime): Datetime to validate.
        field (str): Field name.

    Raises:
        ValueError: If dt is not timezone-aware.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError(f'{field} must be timezone-aware')


def ensure_not_none(value, field: str):
    """Ensures a value is not None.

    Args:
        value: Value to validate.
        field (str): Field name.

    Raises:
        ValueError: If value is None.
    """
    if value is None:
        raise ValueError(f'{field} it is required')
