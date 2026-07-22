from typing import Protocol

from application.dtos.token_dto import PairTokensDTO
from application.dtos.user_dto import UserPublicDTO
from application.ports.output import (
    HasherPort,
    TokenManagerPort,
    UnitOfWorkPort,
)


# ============ User ports ===================
class ChangeEmailCodePort(Protocol):
    """
    Initializes the verification process for changing the user's
    email address, creating a verification code.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token validation and payload
              extraction.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(
        self,
        access: str,
        new_email: str,
        code_expiration_time: int,
    ):
        """
        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `new_email` (str):
                - New email address requested by the user.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

        Raises:
            `InvalidEmailError`:
                - Raised when the provided email is invalid.
            `InvalidTokenError`:
                - Raised when token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `UserNotFoundError`:
                - Raised when no user exists for the authenticated token.
            `InactiveUserError`:
                - Raised when the authenticated user is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - Raised when an unexpected infrastructure failure occurs
                  within an output adapter.
        """
        ...


class ChangeEmailPort(Protocol):
    """
    Change a user's email address.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token validation and
              payload extraction.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str, code: str):
        """
        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code` (str):
                - Verification code sent to the new email address.

        Raises:
            `InvalidTokenError`:
                - If the provided token is malformed, invalid,
                  expired, or cannot be decoded.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `VerificationCodeNotFoundError`:
                - If no verification code exists for the user and
                  provided code.
            `VerificationCodeAlreadyUsedError`:
                - If the verification code was already used.
            `VerificationCodeTypeError`:
                - If the verification code type is invalid for the
                  email change operation.
            `VerificationCodeExpiredError`:
                - If the verification code has expired.
            `UserNotFoundError`:
                - If no user exists for the authenticated token.
            `InactiveUserError`:
                - If the user account is inactive.
            `InvalidEmailError`:
                - If the email extracted from the verification code
                  is invalid.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain entities or value objects.
            `InfrastructureError`:
                - If an unexpected failure occurs in the infrastructure
                  layer during repository, token, or persistence
                  operations.
        """


class ChangePasswordCodePort(Protocol):
    """
    Initializes the verification process for changing the user's
    password, creating a verification code.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation and decoding.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str, code_expiraton_time: int):
        """
        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

        Raises:
            `InvalidTokenError`:
                - Raised when the provided token is invalid, expired,
                  malformed, or contains invalid claims.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `UserNotFoundError`:
                - Raised when the authenticated user no longer exists.
            `InactiveUserError`:
                - Raised when the authenticated user is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted user data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - Raised when persistence operations, token operations,
                  transaction handling, or external infrastructure services
                  fail unexpectedly.
        """
        ...


class ChangePasswordPort(Protocol):
    """
    Change a user's password.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
        `hasher` (HasherPort):
            - Service responsible for password hashing operations.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
        hasher: HasherPort,
    ): ...

    async def execute(
        self,
        access: str,
        code: str,
        new_password: str,
        new_password_confirmation: str,
    ):
        """
        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code` (str):
                - Verification code authorizing the password change.
            `new_password` (str):
                - New raw password provided by the user.
            `new_password_confirmation` (str):
                - Confirmation password used to validate consistency.

        Raises:
            `InvalidPasswordError`:
                - If password policy validation fails.
            `PasswordMismatchError`:
                - If password confirmation does not match.
            `InfrastructureError`:
                - If hashing, repositories, transactions,
                  or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `UserNotFoundError`:
                - If authenticated user cannot be found.
            `InactiveUserError`:
                - If authenticated user is inactive.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist.
            `VerificationCodeAlreadyUsedError`:
                - If verification code was already consumed.
            `VerificationCodeTypeError`:
                - If verification code type is invalid.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
        """
        ...


class DeleteAccountCodePort(Protocol):
    """
    Initializes the verification process for delete the user,
    creating a verification code.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation and decoding.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str, code_expiration_time: int):
        """
        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

        Raises:
            `InvalidTokenError`:
                - Raised when the provided token is invalid, expired,
                  malformed, or contains invalid claims.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `UserNotFoundError`:
                - Raised when the authenticated user no longer exists.
            `InactiveUserError`:
                - Raised when the authenticated user is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted user data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - Raised when persistence operations, token operations,
                  transaction handling, or external infrastructure services
                  fail unexpectedly.
        """
        ...


class DeleteAccountPort(Protocol):
    """
    Delete user.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation and decoding.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str, code: str):
        """
        Executes the authenticated account deletion flow.

        Args:
            `access` (str):
                - Authenticated access token associated with the user.
            `code` (str):
                - Verification code authorizing account deletion.

        Raises:
            `InvalidTokenError`:
                - If token validation fails at domain level.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `InfrastructureError`:
                - If token decoding, persistence, or transactional
                  operations fail unexpectedly.
            `UserNotFoundError`:
                - If authenticated user cannot be found.
            `InactiveUserError`:
                - If authenticated user is inactive.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist.
            `VerificationCodeAlreadyUsedError`:
                - If verification code was already consumed.
            `VerificationCodeTypeError`:
                - If verification code is not DELETE_ACCOUNT type.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
        """
        ...


class DetailPort(Protocol):
    """
    Retrieves authenticated user details from a valid access token.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token validation and
              payload extraction.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str) -> UserPublicDTO:
        """
        Args:
            `access` (str):
                - Authenticated access token associated with the user.

        Returns:
            `UserPublicDTO`:
                - Public-safe representation of the authenticated user.

        Raises:
            `InvalidTokenError`:
                - Raised when token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not an access token.
            `UserNotFoundError`:
                - If no user exists for the token subject.
            `InactiveUserError`:
                - If user account is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output
                  adapter (infrastructure layer).
        """
        ...


class EmailVerificationCodePort(Protocol):
    """
    Initializes the verification process for the user's
    email verification, creating a verification code.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(self, uow: UnitOfWorkPort): ...

    async def execute(
        self,
        email: str,
        code_expiration_time: int,
    ):
        """Generates a code and persists an email verification message.

        Args:
            `email` (str):
                - User email address used to identify the account.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

        Raises:
            `UserNotFoundError`:
                - If no user exists with the provided email.
            `EmailAlreadyVerifiedError`:
                - If user's email is already verified.
            `InactiveUserError`:
                - If user account is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output adapter
                  (infrastructure layer)
        """
        ...


class EmailVerificationPort(Protocol):
    """
    Completes the user email verification process.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(
        self,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, email: str, code: str):
        """
        Verifies a user's email using a verification code.

        Args:
            `email` (str):
                - User email address associated with the account.
            `code` (str):
                - Verification code informed by the user.

        Raises:
            `UserNotFoundError`:
                - If no user exists with the provided email.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist for the user and code.
            `EmailAlreadyVerifiedError`:
                - If user's email is already verified.
            `InactiveUserError`:
                - If user account is inactive.
            `VerificationCodeAlreadyUsedError`:
                - If verification code was already used.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
            `VerificationCodeTypeError`:
                - If verification code type is incorrect.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output adapter
                  (infrastructure layer)
        """
        ...


class RegisterUserPort(Protocol):
    """
    Register a user.

    Attributes:
        `hasher` (HasherPort):
            - Port/Interface responsible for hashing raw passwords securely.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(self, hasher: HasherPort, uow: UnitOfWorkPort): ...

    async def execute(self, email: str, raw_password: str) -> UserPublicDTO:
        """
        Args:
            `email` (str):
                - User email address used to identify the account.
            `raw_password` (str):
                - The plain-text password provided by the user,
                  which will be validated and hashed before storage.

        Raises:
            `InvalidEmailError`:
                - Raised when the email is invalid.
            `InvalidPasswordError`:
                - Raised when the password does not satisfy the
                  password policy.
            `EmailAlreadyUsedError`:
                - Raised when the email is already being used by another user.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output adapter
                  (infrastructure layer)
        """
        ...


class ResetPasswordCodePort(Protocol):
    """
    Initializes the verification process for reset the user's
    password, creating a verification code.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(self, uow: UnitOfWorkPort): ...

    async def execute(
        self,
        email: str,
        code_expiration_time: int,
    ):
        """
        Args:
            `email` (str):
                - User email address associated with the account.
            `code_expiration_time` (int):
                - Verification code expiration time in minutes.

        Raises:
            `UserNotFoundError`:
                - If no user exists with the provided email.
            `InactiveUserError`:
                - If user account is inactive.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output adapter
                  (infrastructure layer)
        """
        ...


class ResetPasswordPort(Protocol):
    """
    Completes the password reset process for a user.

    Attributes:
        `hasher` (HasherPort):
            - Port/Interface responsible for securely hashing raw
              passwords.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(
        self,
        hasher: HasherPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(
        self,
        email: str,
        code: str,
        raw_password: str,
        raw_password_confirmation: str,
    ):
        """
        Args:
            `email` (str):
                - User email address associated with the account.
            `code` (str):
                - Verification code informed by the user.
            `raw_password` (str):
                - New raw password informed by the user.
            `raw_password_confirmation` (str):
                - Confirmation password used to validate equality with
                  the new password.

        Raises:
            `InvalidPasswordError`:
                - Raised when the password does not satisfy the
                  password policy.
            `PasswordMismatchError`:
                - Raised when password and confirmation password do
                  not match.
            `UserNotFoundError`:
                - If no user exists with the provided email.
            `InactiveUserError`:
                - If user account is inactive.
            `VerificationCodeNotFoundError`:
                - If verification code does not exist for the user
                  and code.
            `VerificationCodeAlreadyUsedError`:
                - If verification code was already used.
            `VerificationCodeExpiredError`:
                - If verification code has expired.
            `VerificationCodeTypeError`:
                - If verification code type is incorrect.
            `CorruptedPersistenceStateError`:
                - Raised when persisted data cannot be reconstructed
                  into valid domain objects.
            `InfrastructureError`:
                - If an unexpected failure occurs within an output
                  adapter (infrastructure layer)
        """
        ...


# ============= Authentication ports ====================
class LoginPort(Protocol):
    """
    Handles user authentication and issues access/refresh tokens.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port/Interface responsible for token generation and
            session management.
        `hasher` (HasherPort):
            - Port/Interface responsible for securely verifying raw passwords.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        hasher: HasherPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, email: str, password: str) -> PairTokensDTO:
        """
        Executes the authentication flow.

        Args:
            `email` (str):
                - User email used for authentication lookup.
            `password` (str):
                - Plain password provided by the user.

        Returns:
            `PairTokensDTO`:
                - Access and refresh tokens for authenticated session.

        Raises:
            `InvalidCredentialsError`:
                - If user does not exist or password is invalid.
            `InactiveUserError`:
                - If user account is inactive.
            `UnverifiedEmailError`:
                - If user email has not been verified.
            `InfrastructureError`:
                - If repository, hashing, or token generation fails.
        """
        ...


class RefreshPort(Protocol):
    """
    Handles the refresh access token workflow.

    Args:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation and generation.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for managing atomic database
              transactions across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, refresh: str) -> str:
        """
        Executes the refresh access token flow.

        Args:
            `refresh` (str):
                - Refresh token.

        Raises:
            `InfrastructureError`:
                - If token validation, repositories, or token
                  generation operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not a refresh token.
            `TokenNotFoundError`:
                - If refresh token does not exist.
            `TokenRevokedError`:
                - If refresh token has been revoked.
            `UserNotFoundError`:
                - If authenticated user cannot be found.
            `InactiveUserError`:
                - If authenticated user is inactive.
            `CorruptedPersistenceStateError`:
                - If persisted user state is corrupted.
        """
        ...


class RevokeAllRefreshesPort(Protocol):
    """
    Handles the refresh token mass revocation workflow.

    Args:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, refresh: str):
        """
        Executes the mass refresh token revocation flow.

        Args:
            `refresh` (str):
                - Refresh token.

        Raises:
            `InfrastructureError`:
                - If token validation or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not a refresh token.
        """
        ...


class RevokeRefreshPort(Protocol):
    """
    Handles the refresh token revocation workflow.

    Args:
        `token_manager` (TokenManagerPort):
            - Service responsible for token validation.
        `uow` (UnitOfWorkPort):
            - Port/Interface responsible for coordinating atomic
              transactional operations across repositories.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, refresh: str):
        """
        Executes the refresh token revocation flow.

        Args:
            `refresh` (str):
                - Refresh token.

        Raises:
            `InfrastructureError`:
                - If token validation or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not a refresh token.
        """
        ...
