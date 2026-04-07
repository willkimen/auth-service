import uuid
from datetime import datetime, timezone

from domain.user import User


def create_new_user(email: str, plain_password: str) -> User:
    """Creates a new user with default initial state.

    Generates public_id and sets timestamps using current UTC.

    Args:
        email (str): User email.
        plain_password (str): Raw password.

    Returns:
        User: Created user.

    Raises:
        InvalidEmailError: If email is invalid.
        InvalidPasswordError: If password is invalid.
    """
    now = datetime.now(timezone.utc)

    return User(
        public_id=uuid.uuid4(),
        email=email,
        plain_password=plain_password,
        email_verified=False,
        is_active=False,
        created_at=now,
        updated_at=now,
        last_login_at=None,
    )
