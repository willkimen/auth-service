import uuid
from datetime import datetime, timezone

from domain.user import User


def create_new_user(email: str, plain_password: str) -> User:
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
