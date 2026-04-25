import uuid
from datetime import datetime

from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.value_objects.code import Code
from domain.value_objects.email import Email


def new_email_verification_code(
    user_public_id: uuid.UUID,
    code: Code | None,
    created_at: datetime,
    expires_at: datetime,
    sent_at: datetime | None,
) -> VerificationCode:
    """
    Creates an email verification code.

    Args:
        `user_public_id` (UUID): Owner user identifier.
        `code` (Code | None): Code instance or None to auto-generate.
        `created_at` (datetime): Creation timestamp.
        `expires_at` (datetime): Expiration timestamp.
        `sent_at` (datetime): Send timestamp.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError:
            - If `user_public_id` is None.
            - If `created_at` is None.
            - If `expires_at` is None.
        InvalidTimestampError:
            - If `created_at` has no timezone information.
            - If `expires_at` has no timezone information.
            - If `expires_at` is earlier than `created_at`.
            - If `used_at` has no timezone information.
            - If `used_at` is earlier than `created_at`.
            - If `sent_at` has no timezone information.
            - If `sent_at` is earlier than `created_at`.
        TypeError:
            - If `user_public_id` is not UUID type.
    """
    return VerificationCode(
        code=code,
        user_public_id=user_public_id,
        type=CodeType.EMAIL_VERIFICATION,
        created_at=created_at,
        expires_at=expires_at,
        sent_at=sent_at,
    )


def new_change_email_code(
    user_public_id: uuid.UUID,
    code: Code | None,
    created_at: datetime,
    expires_at: datetime,
    sent_at: datetime | None,
    new_email: str,
) -> VerificationCode:
    """
    Creates an email change verification code.

    Args:
        `user_public_id` (UUID): Owner user identifier.
        `code` (Code | None): Code instance or None to auto-generate.
        `created_at` (datetime): Creation timestamp.
        `expires_at` (datetime): Expiration timestamp.
        `sent_at` (datetime): Send timestamp.
        `new_email` (str): New email value.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError:
            - If `user_public_id` is None.
            - If `created_at` is None.
            - If `expires_at` is None.
        InvalidTimestampError:
            - If `created_at` has no timezone information.
            - If `expires_at` has no timezone information.
            - If `expires_at` is earlier than `created_at`.
            - If `used_at` has no timezone information.
            - If `used_at` is earlier than `created_at`.
            - If `sent_at` has no timezone information.
            - If `sent_at` is earlier than `created_at`.
        TypeError:
            - If `user_public_id` is not UUID type.
        InvalidEmailError:
            - If `new_email` is None, empty, or invalid.
    """
    Email(new_email)

    return VerificationCode(
        code=code,
        user_public_id=user_public_id,
        type=CodeType.CHANGE_EMAIL,
        created_at=created_at,
        expires_at=expires_at,
        sent_at=sent_at,
        payload={'new_email': new_email},
    )


def new_change_password_code(
    user_public_id: uuid.UUID,
    code: Code | None,
    created_at: datetime,
    expires_at: datetime,
    sent_at: datetime | None,
) -> VerificationCode:
    """
    Creates a password change verification code.

    Args:
        `user_public_id` (UUID): Owner user identifier.
        `code` (Code | None): Code instance or None to auto-generate.
        `created_at` (datetime): Creation timestamp.
        `expires_at` (datetime): Expiration timestamp.
        `sent_at` (datetime): Send timestamp.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError:
            - If `user_public_id` is None.
            - If `created_at` is None.
            - If `expires_at` is None.
        InvalidTimestampError:
            - If `created_at` has no timezone information.
            - If `expires_at` has no timezone information.
            - If `expires_at` is earlier than `created_at`.
            - If `used_at` has no timezone information.
            - If `used_at` is earlier than `created_at`.
            - If `sent_at` has no timezone information.
            - If `sent_at` is earlier than `created_at`.
        TypeError:
            - If `user_public_id` is not UUID type.
    """
    return VerificationCode(
        code=code,
        user_public_id=user_public_id,
        type=CodeType.CHANGE_PASSWORD,
        created_at=created_at,
        expires_at=expires_at,
        sent_at=sent_at,
    )


def new_reset_password_code(
    user_public_id: uuid.UUID,
    code: Code | None,
    created_at: datetime,
    expires_at: datetime,
    sent_at: datetime | None,
) -> VerificationCode:
    """
    Creates a password reset verification code.

    Args:
        `user_public_id` (UUID): Owner user identifier.
        `code` (Code | None): Code instance or None to auto-generate.
        `created_at` (datetime): Creation timestamp.
        `expires_at` (datetime): Expiration timestamp.
        `sent_at` (datetime): Send timestamp.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError:
            - If `user_public_id` is None.
            - If `created_at` is None.
            - If `expires_at` is None.
        InvalidTimestampError:
            - If `created_at` has no timezone information.
            - If `expires_at` has no timezone information.
            - If `expires_at` is earlier than `created_at`.
            - If `used_at` has no timezone information.
            - If `used_at` is earlier than `created_at`.
            - If `sent_at` has no timezone information.
            - If `sent_at` is earlier than `created_at`.
        TypeError:
            - If `user_public_id` is not UUID type.
    """
    return VerificationCode(
        code=code,
        user_public_id=user_public_id,
        type=CodeType.RESET_PASSWORD,
        created_at=created_at,
        expires_at=expires_at,
        sent_at=sent_at,
    )


def new_delete_account_code(
    user_public_id: uuid.UUID,
    code: Code | None,
    created_at: datetime,
    expires_at: datetime,
    sent_at: datetime | None,
) -> VerificationCode:
    """
    Creates an account deletion verification code.

    Args:
        `user_public_id` (UUID): Owner user identifier.
        `code` (Code | None): Code instance or None to auto-generate.
        `created_at` (datetime): Creation timestamp.
        `expires_at` (datetime): Expiration timestamp.
        `sent_at` (datetime): Send timestamp.

    Returns:
        VerificationCode: Created verification code.

    Raises:
        RequiredFieldError:
            - If `user_public_id` is None.
            - If `created_at` is None.
            - If `expires_at` is None.
        InvalidTimestampError:
            - If `created_at` has no timezone information.
            - If `expires_at` has no timezone information.
            - If `expires_at` is earlier than `created_at`.
            - If `used_at` has no timezone information.
            - If `used_at` is earlier than `created_at`.
            - If `sent_at` has no timezone information.
            - If `sent_at` is earlier than `created_at`.
        TypeError:
            - If `user_public_id` is not UUID type.
    """
    return VerificationCode(
        code=code,
        user_public_id=user_public_id,
        type=CodeType.DELETE_ACCOUNT,
        created_at=created_at,
        expires_at=expires_at,
        sent_at=sent_at,
    )
