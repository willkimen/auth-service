from datetime import datetime
from typing import Protocol

from application.dto.token_dto import (
    PairTokensDTO,
    PayloadTokenDTO,
)
from application.dto.user_dto import UserPersistenceDTO
from application.dto.verification_code_dto import (
    VerificationCodePersistenceDTO,
)
from application.events.integration_events import IntegrationEvent


class UserRepositoryPort(Protocol):
    """Defines persistence operations for User entities."""

    async def create(self, user_record: UserPersistenceDTO):
        """Persists a new user record.

        Raises:
            InfrastructureError:
                If database insertion fails or is unavailable.
        """
        ...

    async def update(self, user_record: UserPersistenceDTO):
        """Updates an existing user record.

        Raises:
            InfrastructureError:
                If database update operation fails.
        """
        ...

    async def delete(self, public_id: str):
        """Deletes a user by public identifier.

        Raises:
            InfrastructureError:
                If delete operation fails in the database.
        """
        ...

    async def get_by_email(self, email: str) -> UserPersistenceDTO | None:
        """Retrieves a user by email.

        Raises:
            InfrastructureError:
                If query execution fails.
        """
        ...

    async def get_by_public_id(
        self, public_id: str
    ) -> UserPersistenceDTO | None:
        """Retrieves a user by public identifier.

        Raises:
            InfrastructureError:
                If query execution fails.
        """
        ...

    async def exists_by_email(self, email: str) -> bool:
        """Checks if a user exists by email.

        Raises:
            InfrastructureError:
                If database check fails.
        """
        ...

    async def exists_by_public_id(self, public_id: str) -> bool:
        """Checks if a user exists by public identifier.

        Raises:
            InfrastructureError:
                If database check fails.
        """
        ...

    async def is_active(self, public_id: str) -> bool:
        """Checks if a user is active.

        Raises:
            InfrastructureError:
                If database query fails.
        """
        ...


class VerificationCodeRepositoryPort(Protocol):
    """Defines persistence operations for verification codes."""

    async def create(self, code_record: VerificationCodePersistenceDTO):
        """Persists a verification code.

        Raises:
            InfrastructureError:
                If database insert fails.
        """
        ...

    async def update(self, code_record: VerificationCodePersistenceDTO):
        """Updates a verification code record.

        Raises:
            InfrastructureError:
                If database update fails.
        """
        ...

    async def get_by_user_id_and_code(
        self, user_public_id: str, code: str
    ) -> VerificationCodePersistenceDTO | None:
        """Retrieves a verification code by user and code value.

        Raises:
            InfrastructureError:
                If query execution fails.
        """
        ...

    async def delete_all(self, public_id: str):
        """Deletes all verification codes for a user.

        Raises:
            InfrastructureError:
                If delete operation fails.
        """
        ...


class TokenRepositoryPort(Protocol):
    """Defines persistence operations for tokens."""

    async def save_refresh(self, sub: str, jti: str, expires_at: datetime):
        """Stores a refresh token.

        Raises:
            InfrastructureError:
                If persistence operation fails
                (database unavailable, query failure).
        """
        ...

    async def revoke_all_refreshes(self, sub: str):
        """Revokes all refresh tokens for a subject.

        Raises:
            InfrastructureError:
                If update operation fails.
        """
        ...

    async def exists(self, jti: str) -> bool:
        """Checks if a token exists.

        Raises:
            InfrastructureError:
                If query fails.
        """
        ...

    async def is_revoke(self, jti: str) -> bool:
        """Checks if a token is revoked.

        Raises:
            InfrastructureError:
                If query fails.
        """
        ...


class UnitOfWorkPort(Protocol):
    """Defines transactional boundaries for application operations."""

    async def __enter__(self) -> 'UnitOfWorkPort':
        """Starts a transaction context.

        Raises:
            InfrastructureError:
                If transaction initialization fails.
        """
        ...

    async def __exit__(self, exc_type, exc_value, traceback):
        """Ends a transaction, committing or rolling back.

        Raises:
            InfrastructureError:
                If commit or rollback fails.
        """
        ...


class HasherPort(Protocol):
    """Defines password hashing and verification operations."""

    def hash(self, raw_password: str) -> str:
        """Hashes a raw password into a secure representation.

        Raises:
            InfrastructureError:
                If hashing algorithm or cryptographic library fails.
        """
        ...

    def verify_password(
        self, plain_password: str, hashed_password: str
    ) -> bool:
        """Verifies if a plain password matches a hashed password.

        Raises:
            InfrastructureError:
                If verification process fails due to cryptographic
                or hashing backend issues.
        """
        ...


class MessagePublisherPort(Protocol):
    """Defines integration event publishing operations."""

    async def publish(self, integration_event: IntegrationEvent) -> None:
        """Registers an integration event for asynchronous delivery.

        The event will be processed and delivered to external systems
        outside the current transaction boundary.

        Raises:
            InfrastructureError:
                If event persistence or dispatch scheduling fails.
        """
        ...


class TokenManagerPort(Protocol):
    """Defines token generation and validation operations."""

    def new_pair_token(self, sub: str) -> PairTokensDTO:
        """Generates access and refresh token pair.

        Raises:
            InfrastructureError:
                If underlying JWT library or signing mechanism fails.
        """
        ...

    def new_access(self, sub: str) -> str:
        """Generates a new access token.

        Raises:
            InfrastructureError:
                If token signing or encoding fails unexpectedly.
        """
        ...

    def validate(self, token: str) -> PayloadTokenDTO:
        """Validates and decodes a JWT token.

        Raises:
            TokenError:
                If token is invalid at application level:
                - expired
                - malformed
                - invalid signature
                - invalid claims
            InfrastructureError:
                If token decoding library fails unexpectedly.
        """
        ...
