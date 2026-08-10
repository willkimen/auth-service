from typing import Protocol

from auth_service.application.dtos.token_dto import PairTokensDTO
from auth_service.application.dtos.user_dto import UserPublicDTO
from auth_service.application.ports.output import (
    HasherPort,
    TokenManagerPort,
    UnitOfWorkPort,
)


# ============ User ports ===================
class ChangeEmailCodePort(Protocol):
    """
    Defines the contract for initiating the user's email change
    verification process.

    Implementations generate a temporary verification code for the
    requested new email address and persist the data required to
    deliver the code for subsequent processing.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the email change
              verification process.
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
        Initiates the email change verification process for the
        authenticated user.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting the email change.
            `new_email` (str):
                - New email address requested by the authenticated
                  user.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

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
    Defines the contract for completing a user's email change process
    through a previously issued verification code.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the email change.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str, code: str):
        """
        Completes the email change process for the authenticated user
        using a verification code issued for this operation.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting the email change.
            `code` (str):
                - Verification code issued for the email change
                  operation.

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
    Defines the contract for initiating the password change process
    for an authenticated user through a temporary verification code.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the password change
              verification process.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str, code_expiraton_time: int):
        """
        Initiates the password change verification process for the
        authenticated user.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting the password change.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

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
    Defines the contract for completing the password change process
    for an authenticated user using a previously issued verification
    code.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the password change.
        `hasher` (HasherPort):
            - Port responsible for securely hashing the new password
              before it is persisted.
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
        Completes the password change process for the authenticated
        user using a verification code issued for this operation.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting the password change.
            `code` (str):
                - Verification code issued to authorize the password
                  change.
            `new_password` (str):
                - New plain-text password provided by the user.
            `new_password_confirmation` (str):
                - Confirmation of the new password used to verify that
                  both password values match.

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
    Defines the contract for initiating the account deletion process
    for an authenticated user through a temporary verification code.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the account deletion
              verification process.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str, code_expiration_time: int):
        """
        Initiates the account deletion verification process for the
        authenticated user.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting account deletion.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

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
    Defines the contract for completing the account deletion process
    for an authenticated user using a previously issued verification
    code.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the account deletion.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str, code: str):
        """
        Completes the account deletion process for the authenticated
        user using a verification code issued for this operation.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user requesting account deletion.
            `code` (str):
                - Verification code issued to authorize the account
                  deletion.

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
    Defines the contract for retrieving the authenticated user's
    public information from a valid access token.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              identifying the authenticated user.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to retrieve the authenticated user.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str) -> UserPublicDTO:
        """
        Retrieves the public information of the authenticated user
        identified by the provided access token.

        Args:
            `access` (str):
                - Access token used to identify and authenticate the
                  user whose information is being requested.

        Returns:
            `UserPublicDTO`:
                - Public representation of the authenticated user,
                  excluding sensitive information.

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
    Defines the contract for initiating the email verification process
    for a user account through a temporary verification code.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the email verification
              process.
    """

    def __init__(self, uow: UnitOfWorkPort): ...

    async def execute(
        self,
        email: str,
        code_expiration_time: int,
    ):
        """
        Initiates the email verification process for the user account
        associated with the provided email address.

        Args:
            `email` (str):
                - Email address used to identify the user account whose
                  ownership is being verified.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

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
    Defines the contract for completing the email verification process
    for a user account using a previously issued verification code.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the email verification
              process.
    """

    def __init__(
        self,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, email: str, code: str):
        """
        Completes the email verification process for the user account
        associated with the provided email address.

        Args:
            `email` (str):
                - Email address used to identify the user account whose
                  email ownership is being verified.
            `code` (str):
                - Verification code issued for the email verification
                  operation.

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
    Defines the contract for registering a new user account.

    Attributes:
        `hasher` (HasherPort):
            - Port responsible for securely hashing the user's
              password before it is persisted.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to register the new user account.
    """

    def __init__(self, hasher: HasherPort, uow: UnitOfWorkPort): ...

    async def execute(self, email: str, raw_password: str) -> UserPublicDTO:
        """
        Registers a new user account using the provided email address
        and password.

        Args:
            `email` (str):
                - Email address to be associated with the new user
                  account.
            `raw_password` (str):
                - Plain-text password provided by the user. The
                  password is validated and securely hashed before
                  being persisted.

        Returns:
            `UserPublicDTO`:
                - Public representation of the newly registered user,
                  excluding sensitive authentication credentials.

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
    Defines the contract for initiating the password reset process
    for a user account through a temporary verification code.

    Attributes:
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to initiate the password reset
              verification process.
    """

    def __init__(self, uow: UnitOfWorkPort): ...

    async def execute(
        self,
        email: str,
        code_expiration_time: int,
    ):
        """
        Initiates the password reset process for the user account
        associated with the provided email address.

        Args:
            `email` (str):
                - Email address associated with the user account whose
                  password is being reset.
            `code_expiration_time` (int):
                - Duration, in minutes, for which the verification
                  code remains valid.

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
    Defines the contract for completing the password reset process
    for a user account using a previously issued verification code.

    Attributes:
        `hasher` (HasherPort):
            - Port responsible for securely hashing the new password
              before it is persisted.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to complete the password reset.
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
        Completes the password reset process for the user account
        associated with the provided email address using a verification
        code issued for this operation.

        Args:
            `email` (str):
                - Email address associated with the user account whose
                  password is being reset.
            `code` (str):
                - Verification code issued to authorize the password
                  reset.
            `raw_password` (str):
                - New plain-text password provided by the user. The
                  password is validated and securely hashed before
                  being persisted.
            `raw_password_confirmation` (str):
                - Confirmation of the new password used to verify that
                  both password values match.

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
    Defines the contract for authenticating a user and issuing
    authentication tokens for an authenticated session.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for generating authentication tokens
              and managing session-related token state.
        `hasher` (HasherPort):
            - Port responsible for securely verifying the provided
              password against the user's stored password hash.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required during authentication and session
              creation.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        hasher: HasherPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, email: str, password: str) -> PairTokensDTO:
        """
        Authenticates a user using their credentials and creates a new
        authenticated session represented by an access and refresh
        token pair.

        Args:
            `email` (str):
                - Email address used to identify the user account.
            `password` (str):
                - Plain-text password provided for authentication.

        Returns:
            `PairTokensDTO`:
                - Pair containing the access and refresh tokens issued
                  for the newly authenticated session.

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
    Defines the contract for refreshing an authenticated session by
    validating a refresh token and issuing a new access token.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the refresh token and
              generating a new access token.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              operations required to validate the refresh token state
              and retrieve the associated user.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, refresh: str) -> str:
        """
        Validates a refresh token and issues a new access token for
        the associated active user account.

        Args:
            `refresh` (str):
                - Refresh token associated with the authenticated
                  session.

        Returns:
            `str`:
                - Newly issued access token for the authenticated user.

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
    Defines the contract for invalidating all active refresh tokens
    associated with an authenticated user's sessions.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the access token and
              extracting the authenticated user's identity.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              persistence operation required to revoke the user's
              refresh tokens.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, access: str):
        """
        Revokes all refresh tokens associated with the user identified
        by the provided access token, invalidating all active refresh
        token-based sessions for that user.

        Args:
            `access` (str):
                - Access token identifying the authenticated user whose
                  refresh tokens are to be revoked.

        Raises:
            `InfrastructureError`:
                - If token validation or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not a access token.
        """
        ...


class RevokeRefreshPort(Protocol):
    """
    Defines the contract for invalidating a specific refresh token
    associated with an authenticated session.

    Attributes:
        `token_manager` (TokenManagerPort):
            - Port responsible for validating the provided refresh
              token and extracting its token identifier.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating the transactional
              persistence operation required to revoke the refresh
              token.
    """

    def __init__(
        self,
        token_manager: TokenManagerPort,
        uow: UnitOfWorkPort,
    ): ...

    async def execute(self, refresh: str):
        """
        Revokes the refresh token associated with the provided token,
        invalidating the corresponding authenticated session.

        Args:
            `refresh` (str):
                - Refresh token identifying the authenticated session
                  to be invalidated.

        Raises:
            `InfrastructureError`:
                - If token validation or persistence operations fail.
            `InvalidTokenError`:
                - If token validation fails.
            `InvalidTokenTypeError`:
                - If token type is not a refresh token.
        """
        ...
