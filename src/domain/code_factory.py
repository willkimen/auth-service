from datetime import datetime

from domain.code import VerificationCode
from domain.enums import CodeType
from domain.value_objects import Email


def new_activation_account_code(
    user_id: int,
    created_at: datetime,
    expires_at: datetime,
) -> VerificationCode:

    return VerificationCode(
        code=None,
        user_id=user_id,
        type=CodeType.ACCOUNT_ACTIVATION,
        created_at=created_at,
        expires_at=expires_at,
    )


def new_change_email_code(
    user_id: int,
    created_at: datetime,
    expires_at: datetime,
    new_email: str,
) -> VerificationCode:

    Email(new_email)

    return VerificationCode(
        code=None,
        user_id=user_id,
        type=CodeType.CHANGE_EMAIL,
        created_at=created_at,
        expires_at=expires_at,
        payload={'new_email': new_email},
    )


def new_change_password_code(
    user_id: int,
    created_at: datetime,
    expires_at: datetime,
) -> VerificationCode:

    return VerificationCode(
        code=None,
        user_id=user_id,
        type=CodeType.CHANGE_PASSWORD,
        created_at=created_at,
        expires_at=expires_at,
    )


def new_reset_password_code(
    user_id: int,
    created_at: datetime,
    expires_at: datetime,
) -> VerificationCode:

    return VerificationCode(
        code=None,
        user_id=user_id,
        type=CodeType.RESET_PASSWORD,
        created_at=created_at,
        expires_at=expires_at,
    )


def new_delete_account_code(
    user_id: int,
    created_at: datetime,
    expires_at: datetime,
) -> VerificationCode:

    return VerificationCode(
        code=None,
        user_id=user_id,
        type=CodeType.DELETE_ACCOUNT,
        created_at=created_at,
        expires_at=expires_at,
    )
