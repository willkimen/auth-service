import uuid
from dataclasses import dataclass
from datetime import datetime

from domain.entities.user import User


@dataclass(frozen=True)
class UserPublicDTO:
    """
    Represents a public DTO for User entities.
    Exposes only safe and public user data.
    """

    public_id: uuid.UUID
    email: str
    email_verified: bool
    created_at: datetime
    last_login_at: datetime | None

    @classmethod
    def from_entity(cls, user: User) -> 'UserPublicDTO':
        """
        Creates a public DTO from a User entity.

        Args:
            user (User): Source entity.

        Returns:
            UserPublicDTO: Created DTO.
        """
        return cls(
            public_id=user.public_id,
            email=user.email.value,
            email_verified=user.email_verified,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
