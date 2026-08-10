from typing import Annotated

from fastapi import Depends

from auth_service.adapters.inputs.api.dependencies.adapters import (
    HasherDep,
    TokenManagerDep,
    UnitOfWorkDep,
)
from auth_service.application.ports.input import (
    ChangeEmailCodePort,
    ChangeEmailPort,
    ChangePasswordCodePort,
    ChangePasswordPort,
    DeleteAccountCodePort,
    DeleteAccountPort,
    DetailPort,
    EmailVerificationCodePort,
    EmailVerificationPort,
    LoginPort,
    RefreshPort,
    RegisterUserPort,
    ResetPasswordCodePort,
    ResetPasswordPort,
    RevokeAllRefreshesPort,
    RevokeRefreshPort,
)
from auth_service.application.use_cases.authentication.login import (
    LoginUseCase,
)
from auth_service.application.use_cases.authentication.refresh import (
    RefreshUseCase,
)
from auth_service.application.use_cases.authentication.revoke_all_refreshes import (
    RevokeAllRefreshesUseCase,
)
from auth_service.application.use_cases.authentication.revoke_refresh import (
    RevokeRefreshUseCase,
)
from auth_service.application.use_cases.user.change_email import (
    ChangeEmailUseCase,
)
from auth_service.application.use_cases.user.change_email_code import (
    ChangeEmailCodeUseCase,
)
from auth_service.application.use_cases.user.change_password import (
    ChangePasswordUseCase,
)
from auth_service.application.use_cases.user.change_password_code import (
    ChangePasswordCodeUseCase,
)
from auth_service.application.use_cases.user.delete_account import (
    DeleteAccountUseCase,
)
from auth_service.application.use_cases.user.delete_account_code import (
    DeleteAccountCodeUseCase,
)
from auth_service.application.use_cases.user.detail import DetailUseCase
from auth_service.application.use_cases.user.email_verification import (
    EmailVerificationUseCase,
)
from auth_service.application.use_cases.user.email_verification_code import (
    EmailVerificationCodeUseCase,
)
from auth_service.application.use_cases.user.register import (
    RegisterUserUseCase,
)
from auth_service.application.use_cases.user.reset_password import (
    ResetPasswordUseCase,
)
from auth_service.application.use_cases.user.reset_password_code import (
    ResetPasswordCodeUseCase,
)


def register_factory(
    hasher: HasherDep,
    uow: UnitOfWorkDep,
) -> RegisterUserPort:
    """
    Creates the user registration use case.

    Args:
        `hasher` (`HasherPort`):
            - Password hashing adapter used to securely hash user passwords.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `RegisterUserPort`:
            - User registration use case.
    """
    return RegisterUserUseCase(hasher, uow)


RegisterUseCaseDep = Annotated[RegisterUserPort, Depends(register_factory)]


def detail_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> DetailPort:
    """
    Creates the authenticated user detail use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate and decode
              authentication tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `DetailPort`:
            - Authenticated user detail use case.
    """
    return DetailUseCase(token_manager, uow)


DetailUserDep = Annotated[DetailPort, Depends(detail_factory)]


def email_verification_code_factory(
    uow: UnitOfWorkDep,
) -> EmailVerificationCodePort:
    """
    Creates the email verification code use case.

    Args:
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `EmailVerificationCodePort`:
            - Email verification code use case.
    """
    return EmailVerificationCodeUseCase(uow)


EmailVerificationCodeDep = Annotated[
    EmailVerificationCodePort, Depends(email_verification_code_factory)
]


def email_verification_factory(
    uow: UnitOfWorkDep,
) -> EmailVerificationPort:
    """
    Creates the email verification use case.

    Args:
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `EmailVerificationPort`:
            - Email verification use case.
    """
    return EmailVerificationUseCase(uow)


EmailVerificationDep = Annotated[
    EmailVerificationPort, Depends(email_verification_factory)
]


def change_email_code_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> ChangeEmailCodePort:
    """
    Creates the email change code use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate and decode
              authentication tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `ChangeEmailCodePort`:
            - Email change code use case.
    """
    return ChangeEmailCodeUseCase(token_manager, uow)


ChangeEmailCodeDep = Annotated[ChangeEmailCodePort, Depends(change_email_code_factory)]


def change_email_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> ChangeEmailPort:
    """
    Creates the email change use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate and decode
              authentication tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `ChangeEmailPort`:
            - Email change use case.
    """
    return ChangeEmailUseCase(token_manager, uow)


ChangeEmailDep = Annotated[ChangeEmailPort, Depends(change_email_factory)]


def change_password_code_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> ChangePasswordCodePort:
    """
    Creates the password change code use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate and decode
              authentication tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `ChangePasswordCodePort`:
            - Password change code use case.
    """
    return ChangePasswordCodeUseCase(token_manager, uow)


ChangePasswordCodeDep = Annotated[
    ChangePasswordCodePort, Depends(change_password_code_factory)
]


def change_password_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
    hasher: HasherDep,
) -> ChangePasswordPort:
    """
    Creates the password change use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate and decode
              authentication tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.
        `hasher` (`HasherPort`):
            - Password hashing adapter used to securely hash and verify
              passwords.

    Returns:
        `ChangePasswordPort`:
            - Password change use case.
    """
    return ChangePasswordUseCase(token_manager, uow, hasher)


ChangePasswordDep = Annotated[ChangePasswordPort, Depends(change_password_factory)]


def reset_password_code_factory(
    uow: UnitOfWorkDep,
) -> ResetPasswordCodePort:
    """
    Creates the password reset code use case.

    Args:
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `ResetPasswordCodePort`:
            - Password reset code use case.
    """
    return ResetPasswordCodeUseCase(uow)


ResetPasswordCodeDep = Annotated[
    ResetPasswordCodePort, Depends(reset_password_code_factory)
]


def reset_password_factory(
    hasher: HasherDep,
    uow: UnitOfWorkDep,
) -> ResetPasswordPort:
    """
    Creates the password reset use case.

    Args:
        `hasher` (`HasherPort`):
            - Password hashing adapter used to securely hash passwords.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `ResetPasswordPort`:
            - Password reset use case.
    """
    return ResetPasswordUseCase(hasher, uow)


ResetPasswordDep = Annotated[ResetPasswordPort, Depends(reset_password_factory)]


def delete_account_code_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> DeleteAccountCodePort:
    """
    Creates the account deletion code use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate and decode
              authentication tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `DeleteAccountCodePort`:
            - Account deletion code use case.
    """
    return DeleteAccountCodeUseCase(token_manager, uow)


DeleteAccountCodeDep = Annotated[
    DeleteAccountCodePort, Depends(delete_account_code_factory)
]


def delete_account_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> DeleteAccountPort:
    """
    Creates the account deletion use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate and decode
              authentication tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `DeleteAccountPort`:
            - Account deletion use case.
    """
    return DeleteAccountUseCase(token_manager, uow)


DeleteAccountDep = Annotated[DeleteAccountPort, Depends(delete_account_factory)]


# ============ Use cases - Auth =================


def login_factory(
    token_manager: TokenManagerDep,
    hasher: HasherDep,
    uow: UnitOfWorkDep,
) -> LoginPort:
    """
    Creates the user authentication use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to generate and manage
              authentication tokens.
        `hasher` (`HasherPort`):
            - Password hashing adapter used to securely verify passwords.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `LoginPort`:
            - User authentication use case.
    """
    return LoginUseCase(token_manager, hasher, uow)


LoginDep = Annotated[LoginPort, Depends(login_factory)]


def refresh_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> RefreshPort:
    """
    Creates the access token refresh use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate and generate
              authentication tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `RefreshPort`:
            - Access token refresh use case.
    """
    return RefreshUseCase(token_manager, uow)


RefreshDep = Annotated[RefreshPort, Depends(refresh_factory)]


def revoke_refresh_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> RevokeRefreshPort:
    """
    Creates the refresh token revocation use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate authentication
              tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `RevokeRefreshPort`:
            - Refresh token revocation use case.
    """
    return RevokeRefreshUseCase(token_manager, uow)


RevokeRefreshDep = Annotated[RevokeRefreshPort, Depends(revoke_refresh_factory)]


def revoke_all_refreshes_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> RevokeAllRefreshesPort:
    """
    Creates the mass refresh token revocation use case.

    Args:
        `token_manager` (`TokenManagerPort`):
            - Token management adapter used to validate authentication
              tokens.
        `uow` (`UnitOfWorkPort`):
            - Unit of work responsible for coordinating transactional
              persistence operations.

    Returns:
        `RevokeAllRefreshesPort`:
            - Mass refresh token revocation use case.
    """
    return RevokeAllRefreshesUseCase(token_manager, uow)


RevokeAllRefreshesDep = Annotated[
    RevokeAllRefreshesPort, Depends(revoke_all_refreshes_factory)
]
