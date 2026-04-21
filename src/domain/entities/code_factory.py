from datetime import datetime

from domain.entities.code import VerificationCode
from domain.enums import CodeType
from domain.value_objects.email import Email


def new_email_verification_code(
    user_id: int,
    created_at: datetime,
    expires_at: datetime,
) -> VerificationCode:
    """Creates an email verification code.

    Args:
        user_id (int): Owner user identifier.
        created_at (datetime): Creation timestamp.
        expires_at (datetime): Expiration timestamp.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError: If required fields are None.
        InvalidTimestampError: If timestamps are invalid.
        CodeTypeError: If type is invalid.
        TypeError: If user_id has invalid type.
    """
    return VerificationCode(
        code=None,
        user_id=user_id,
        type=CodeType.EMAIL_VERIFICATION,
        created_at=created_at,
        expires_at=expires_at,
    )


def new_change_email_code(
    user_id: int,
    created_at: datetime,
    expires_at: datetime,
    new_email: str,
) -> VerificationCode:
    """Creates an email change verification code.

    Args:
        user_id (int): Owner user identifier.
        created_at (datetime): Creation timestamp.
        expires_at (datetime): Expiration timestamp.
        new_email (str): New email value.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        InvalidEmailError: If new_email is invalid.
        RequiredFieldError: If required fields are None.
        InvalidTimestampError: If timestamps are invalid.
        CodeTypeError: If type is invalid.
        TypeError: If user_id has invalid type.
    """

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
    """Creates a password change verification code.

    Args:
        user_id (int): Owner user identifier.
        created_at (datetime): Creation timestamp.
        expires_at (datetime): Expiration timestamp.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError: If required fields are None.
        InvalidTimestampError: If timestamps are invalid.
        CodeTypeError: If type is invalid.
        TypeError: If user_id has invalid type.
    """
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
    """Creates a password reset verification code.

    Args:
        user_id (int): Owner user identifier.
        created_at (datetime): Creation timestamp.
        expires_at (datetime): Expiration timestamp.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError: If required fields are None.
        InvalidTimestampError: If timestamps are invalid.
        CodeTypeError: If type is invalid.
        TypeError: If user_id has invalid type.
    """
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
    """Creates an account deletion verification code.

    Args:
        user_id (int): Owner user identifier.
        created_at (datetime): Creation timestamp.
        expires_at (datetime): Expiration timestamp.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError: If required fields are None.
        InvalidTimestampError: If timestamps are invalid.
        CodeTypeError: If type is invalid.
        TypeError: If user_id has invalid type.
    """
    return VerificationCode(
        code=None,
        user_id=user_id,
        type=CodeType.DELETE_ACCOUNT,
        created_at=created_at,
        expires_at=expires_at,
    )
