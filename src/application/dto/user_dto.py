import uuid
from dataclasses import dataclass
from datetime import datetime

from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


@dataclass(frozen=True)
class UserPersistenceDTO:
    """
    Represents a persistence DTO for User entities.
    Used to transfer user data between domain and persistence layers.
    """

    public_id: uuid.UUID
    email: str
    hash_password: str
    email_verified: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    @classmethod
    def from_entity(cls, user: User) -> 'UserPersistenceDTO':
        """
        Creates a persistence DTO from a User entity.

        Args:
            user (User): Source entity.

        Returns:
            UserPersistenceDTO: Created DTO.
        """
        return cls(
            public_id=user.public_id,
            email=user.email.value,
            hash_password=user.hash_password.value,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )

    def to_entity(self) -> User:
        """
        Converts persistence data into a User entity.

        Returns:
            User: Reconstructed entity.

        Raises:
            ValueError:
                - If `public_id` is None.
                - If `email_verified` is None.
                - If `is_active` is None.
                - If `created_at` is None.
                - If `updated_at` is None.
                - If `created_at` has no timezone information.
                - If `updated_at` has no timezone information.
                - If `updated_at` is earlier than `created_at`.
                - If `last_login_at` has no timezone information.
                - If `last_login_at` is earlier than `created_at`.
            TypeError:
                - If `public_id` is not UUID type.
                - If `email_verified` is not bool type.
                - If `is_active` is not bool type.
        """
        return User(
            public_id=self.public_id,
            email=Email(self.email),
            hash_password=PasswordHash(self.hash_password),
            email_verified=self.email_verified,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at,
            last_login_at=self.last_login_at,
        )


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
