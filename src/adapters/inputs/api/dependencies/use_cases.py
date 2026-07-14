from typing import Annotated

from fastapi import Depends

from adapters.inputs.api.dependencies.adapters import (
    HasherDep,
    TokenManagerDep,
    UnitOfWorkDep,
)
from application.ports.input import (
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
from application.use_cases.authentication.login import LoginUseCase
from application.use_cases.authentication.refresh import RefreshUseCase
from application.use_cases.authentication.revoke_all_refreshes import (
    RevokeAllRefreshesUseCase,
)
from application.use_cases.authentication.revoke_refresh import (
    RevokeRefreshUseCase,
)
from application.use_cases.user.change_email import (
    ChangeEmailUseCase,
)
from application.use_cases.user.change_email_code import (
    ChangeEmailCodeUseCase,
)
from application.use_cases.user.change_password import (
    ChangePasswordUseCase,
)
from application.use_cases.user.change_password_code import (
    ChangePasswordCodeUseCase,
)
from application.use_cases.user.delete_account import (
    DeleteAccountUseCase,
)
from application.use_cases.user.delete_account_code import (
    DeleteAccountCodeUseCase,
)
from application.use_cases.user.detail import DetailUseCase
from application.use_cases.user.email_verification import (
    EmailVerificationUseCase,
)
from application.use_cases.user.email_verification_code import (
    EmailVerificationCodeUseCase,
)
from application.use_cases.user.register import RegisterUserUseCase
from application.use_cases.user.reset_password import (
    ResetPasswordUseCase,
)
from application.use_cases.user.reset_password_code import (
    ResetPasswordCodeUseCase,
)


def register_factory(
    hasher: HasherDep,
    uow: UnitOfWorkDep,
) -> RegisterUserPort:
    return RegisterUserUseCase(hasher, uow)


RegisterUseCaseDep = Annotated[RegisterUserPort, Depends(register_factory)]


def detail_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> DetailPort:
    return DetailUseCase(token_manager, uow)


DetailUserDep = Annotated[DetailPort, Depends(detail_factory)]


def email_verification_code_factory(
    uow: UnitOfWorkDep,
) -> EmailVerificationCodePort:
    return EmailVerificationCodeUseCase(uow)


EmailVerificationCodeDep = Annotated[
    EmailVerificationCodePort, Depends(email_verification_code_factory)
]


def email_verification_factory(
    uow: UnitOfWorkDep,
) -> EmailVerificationPort:
    return EmailVerificationUseCase(uow)


EmailVerificationDep = Annotated[
    EmailVerificationPort, Depends(email_verification_factory)
]


def change_email_code_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> ChangeEmailCodePort:
    return ChangeEmailCodeUseCase(token_manager, uow)


ChangeEmailCodeDep = Annotated[
    ChangeEmailCodePort, Depends(change_email_code_factory)
]


def change_email_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> ChangeEmailPort:
    return ChangeEmailUseCase(token_manager, uow)


ChangeEmailDep = Annotated[ChangeEmailPort, Depends(change_email_factory)]


def change_password_code_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> ChangePasswordCodePort:
    return ChangePasswordCodeUseCase(token_manager, uow)


ChangePasswordCodeDep = Annotated[
    ChangeEmailCodePort, Depends(change_password_code_factory)
]


def change_password_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
    hasher: HasherDep,
) -> ChangePasswordPort:
    return ChangePasswordUseCase(token_manager, uow, hasher)


ChangePasswordDep = Annotated[
    ChangePasswordPort, Depends(change_password_factory)
]


def reset_password_code_factory(
    uow: UnitOfWorkDep,
) -> ResetPasswordCodePort:
    return ResetPasswordCodeUseCase(uow)


ResetPasswordCodeDep = Annotated[
    ResetPasswordCodePort, Depends(reset_password_code_factory)
]


def reset_password_factory(
    hasher: HasherDep,
    uow: UnitOfWorkDep,
) -> ResetPasswordPort:
    return ResetPasswordUseCase(hasher, uow)


ResetPasswordDep = Annotated[
    ResetPasswordPort, Depends(reset_password_factory)
]


def delete_account_code_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> DeleteAccountCodePort:
    return DeleteAccountCodeUseCase(token_manager, uow)


DeleteAccountCodeDep = Annotated[
    DeleteAccountCodePort, Depends(delete_account_code_factory)
]


def delete_account_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> DeleteAccountPort:
    return DeleteAccountUseCase(token_manager, uow)


DeleteAccountDep = Annotated[
    DeleteAccountPort, Depends(delete_account_factory)
]


# ============ Use cases - Auth =================
def login_factory(
    token_manager: TokenManagerDep,
    hasher: HasherDep,
    uow: UnitOfWorkDep,
) -> LoginPort:
    return LoginUseCase(token_manager, hasher, uow)


LoginDep = Annotated[LoginPort, Depends(login_factory)]


def refresh_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> RefreshPort:
    return RefreshUseCase(token_manager, uow)


RefreshDep = Annotated[RefreshPort, Depends(refresh_factory)]


def revoke_refresh_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> RevokeRefreshPort:
    return RevokeRefreshUseCase(token_manager, uow)


RevokeRefreshDep = Annotated[
    RevokeRefreshPort, Depends(revoke_refresh_factory)
]


def revoke_all_refreshes_factory(
    token_manager: TokenManagerDep,
    uow: UnitOfWorkDep,
) -> RevokeAllRefreshesPort:
    return RevokeAllRefreshesUseCase(token_manager, uow)


RevokeAllRefreshesDep = Annotated[
    RevokeAllRefreshesPort, Depends(revoke_all_refreshes_factory)
]
