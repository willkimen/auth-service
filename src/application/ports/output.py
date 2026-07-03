import uuid
from datetime import datetime
from typing import Protocol

from application.dtos.token_dto import (
    PairTokensDTO,
    PayloadTokenDTO,
)
from application.messages.message import Message
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode


class UserRepositoryPort(Protocol):
    """Defines persistence operations for User entities."""

    async def create(self, user: User) -> None:
        """Persists a new user record.

        Raises:
            InfrastructureError:
                If database insertion fails or is unavailable.
        """
        ...

    async def update(self, user: User) -> None:
        """Updates an existing user record.

        Raises:
            InfrastructureError:
                If database update operation fails.
        """
        ...

    async def delete(self, public_id: uuid.UUID) -> None:
        """Deletes a user by public identifier.

        Raises:
            InfrastructureError:
                If delete operation fails in the database.
        """
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Retrieves a user by email.

        Raises:
            CorruptedPersistenceStateError:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            InfrastructureError:
                If query execution fails.
        """
        ...

    async def get_by_public_id(self, public_id: uuid.UUID) -> User | None:
        """Retrieves a user by public identifier.

        Raises:
            CorruptedPersistenceStateError:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
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


class VerificationCodeRepositoryPort(Protocol):
    """Defines persistence operations for verification codes."""

    async def create(self, verification_code: VerificationCode) -> None:
        """Persists a verification code.

        Raises:
            InfrastructureError:
                If database insert fails.
        """
        ...

    async def mark_as_used(self, verification_code: VerificationCode) -> None:
        """Marks a verification code as used in the database.

        Raises:
            InfrastructureError: If database update fails.
        """
        ...

    async def get_by_user_id_and_code(
        self,
        user_public_id: uuid.UUID,
        code: str,
    ) -> VerificationCode | None:
        """Retrieves a verification code by user and code value.

        Raises:
            CorruptedPersistenceStateError:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            InfrastructureError:
                If query execution fails.
        """
        ...

    async def delete_all(self, user_public_id: uuid.UUID):
        """Deletes all verification codes for a user.

        Raises:
            InfrastructureError:
                If delete operation fails.
        """
        ...


class RefreshTokenRepositoryPort(Protocol):
    """Defines persistence operations for refreshes tokens."""

    async def create(
        self,
        sub: uuid.UUID,
        jti: str,
        expires_at: datetime,
    ) -> None:
        """Stores a refresh token.

        Raises:
            InfrastructureError:
                If persistence operation fails
                (database unavailable, query failure).
        """
        ...

    async def revoke_all(self, sub: uuid.UUID) -> None:
        """Revokes all refresh tokens for a subject.

        Raises:
            InfrastructureError:
                If update operation fails.
        """
        ...

    async def revoke(self, jti: str) -> None:
        """Revoke a specifc refresh token.

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

    async def is_revoked(self, jti: str) -> bool:
        """Checks if a token is revoked.

        Raises:
            InfrastructureError:
                If query fails.
        """
        ...


class MessageRepositoryPort(Protocol):
    """
    Defines persistence operations for messages.

    A persisted message represents an intention to execute
    a specific operation later.

    Messages store all data required for future processing,
    allowing dedicated components or workers to execute
    the intended operation afterwards.
    """

    async def create(self, message: Message) -> None:
        """
        Persists a message containing the data required
        for later processing.

        Raises:
            InfrastructureError:
                Raised when message persistence fails.
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
        self,
        plain_password: str,
        hashed_password: str,
    ) -> bool:
        """Verifies if a plain password matches a hashed password.

        Raises:
            InfrastructureError:
                If verification process fails due to cryptographic
                or hashing backend issues.
        """
        ...


class UnitOfWorkPort(Protocol):
    """
    Defines a transactional persistence context for application use cases.

    A Unit of Work coordinates the lifecycle of the database connection
    and transaction while exposing repository instances that participate
    in the same persistence context. All repository operations performed
    within the Unit of Work share the same connection and are committed
    or rolled back atomically when the context exits.

    Attributes:
        `user_repo` (`UserRepositoryPort`):
            - Repository responsible for user persistence operations.
        `code_repo` (`VerificationCodeRepositoryPort`):
            - Repository responsible for verification code persistence
              operations.
        `message_repo` (`MessageRepositoryPort`):
            - Repository responsible for message persistence operations.
        `token_repo` (`RefreshTokenRepositoryPort`):
            - Repository responsible for refresh token persistence
              operations.
    """

    user_repo: UserRepositoryPort
    code_repo: VerificationCodeRepositoryPort
    message_repo: MessageRepositoryPort
    token_repo: RefreshTokenRepositoryPort

    async def __aenter__(self):
        """
        Enters the transactional persistence context.

        Initializes the underlying database connection, starts a new
        transaction, and makes repository instances available for use.

        Raises:
            InfrastructureError:
                If the persistence context cannot be initialized.
        """
        ...

    async def __aexit__(self, exc_type, exc, tb):
        """
        Exits the transactional persistence context.

        Commits the transaction if no exception occurred; otherwise rolls
        back all changes. Releases the underlying database connection after
        the transaction completes.

        Raises:
            InfrastructureError:
                If transaction finalization fails.
        """
        ...


class TokenManagerPort(Protocol):
    """Defines token generation and validation operations."""

    def new_pair_token(self, sub: uuid.UUID) -> PairTokensDTO:
        """Generates access and refresh token pair.

        Raises:
            InfrastructureError:
                If underlying JWT library or signing mechanism fails.
        """
        ...

    def new_access(self, sub: uuid.UUID) -> str:
        """Generates a new access token.

        Raises:
            InfrastructureError:
                If token signing or encoding fails unexpectedly.
        """
        ...

    def validate(self, token: str) -> PayloadTokenDTO:
        """Validates and decodes a JWT token.

        Raises:
            InvalidTokenError:
                If token is invalid at application level:
                - expired
                - malformed
                - invalid signature
                - invalid claims
            InfrastructureError:
                If token decoding library fails unexpectedly.
        """
        ...
