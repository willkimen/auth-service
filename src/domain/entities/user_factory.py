import uuid
from datetime import datetime, timezone

from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


def create_new_user(email: Email, hash_password: PasswordHash) -> User:
    """Creates a new user with default initial state.

    Generates public_id and sets timestamps using current UTC.

    Args:
        email (Email): Email instance.
        hash_password (PasswordHash): PasswordHash instance.

    Returns:
        User: Created user.
    """
    now = datetime.now(timezone.utc)

    return User(
        public_id=uuid.uuid4(),
        email=email,
        hash_password=hash_password,
        email_verified=False,
        is_active=True,
        created_at=now,
        updated_at=now,
        last_login_at=None,
    )
