from datetime import timezone

from sqlalchemy import Row

from domain.entities.user import User
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash


class UserRowMapper:
    """
    Mapper to convert SQLAlchemy result rows (`Row`) into `User` entity.
    """

    @staticmethod
    def to_domain(row: Row) -> User:
        """Converts a SQLAlchemy `Row` or mapping into a `User` Entity.

        Args:
            `row` (`Row`): The SQLAlchemy result row containing user data.

        Returns:
            `User`: A validated domain `User` instance.

        Raises:
            `DomainError`:
                - If the row data violates domain validation rules or
                  constraints.
            `ValueError`:
                - If any required field is None.
                - If database timestamps are invalid, missing
                  timezone information, or inconsistent.
            `TypeError`:
                - If the data types retrieved from the database
                  do not match domain requirements.
        """
        # ensures UTC timezone on datetimes retrieved from the database
        created_at = row.created_at.replace(tzinfo=timezone.utc)
        updated_at = row.updated_at.replace(tzinfo=timezone.utc)

        last_login_at = None
        if row.last_login_at is not None:
            last_login_at = row.last_login_at.replace(tzinfo=timezone.utc)

        return User(
            public_id=row.public_id,
            email=Email(row.email),
            hash_password=PasswordHash(row.hash_password),
            email_verified=row.email_verified,
            is_active=row.is_active,
            created_at=created_at,
            updated_at=updated_at,
            last_login_at=last_login_at,
        )
