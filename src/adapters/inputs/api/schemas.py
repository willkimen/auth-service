import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr

# =================== Body responses ====================


class UserPublicBodyResponse(BaseModel):
    """
    Public representation of a user response body.

    Attributes:
        `public_id` (`uuid.UUID`):
            - Unique public identifier of the user.
        `email` (`str`):
            - User email address.
        `email_verified` (`bool`):
            - Whether the user's email address has been verified.
        `created_at` (`datetime`):
            - Date and time when the account was created.
        `last_login_at` (`datetime | None`):
            - Date and time of the user's last successful login, if any.
    """

    public_id: uuid.UUID
    email: str
    email_verified: bool
    created_at: datetime
    last_login_at: datetime | None


class AccessBodyResponse(BaseModel):
    """
    Authentication access token response body.

    Attributes:
        `access` (`str`):
            - Access token used to authenticate requests to protected
              endpoints.
    """

    access: str


class TokensBodyResponse(BaseModel):
    """
    Authentication tokens response body.

    Attributes:
        `access` (`str`):
            - Access token used to authenticate requests to protected
              endpoints.

        `refresh` (`str`):
            - Refresh token used to obtain a new access token when the
              current access token expires.
    """

    access: str
    refresh: str


# =================== Body requests ====================


class RefreshBodyRequest(BaseModel):
    """
    Refresh token request body.

    Attributes:
        `refresh` (`str`):
            - Refresh token used to obtain a new access token.
    """

    refresh: str


class CredentialsBodyRequest(BaseModel):
    """
    User authentication credentials request body.

    Attributes:
        `email` (`EmailStr`):
            - User email address.
        `password` (`str`):
            - User password.
    """

    email: EmailStr
    password: str


class EmailBodyRequest(BaseModel):
    """
    Email request body.

    Attributes:
        `email` (`EmailStr`):
            - User email address.
    """

    email: EmailStr


class VerificationCodeBodyRequest(BaseModel):
    """
    Verification code request body.

    Attributes:
        `code` (`str`):
            - Verification code.
    """

    code: str


class EmailAndCodeBodyRequest(BaseModel):
    """
    Email verification request body.

    Attributes:
        `email` (`EmailStr`):
            - User email address.
        `code` (`str`):
            - Verification code.
    """

    email: EmailStr
    code: str


class ResetPasswordBodyRequest(BaseModel):
    """
    Password reset request body.

    Attributes:
        `email` (`EmailStr`):
            - User email address.
        `code` (`str`):
            - Password reset verification code.
        `password` (`str`):
            - New password.
        `password_confirmation` (`str`):
            - Confirmation of the new password.
    """

    email: EmailStr
    code: str
    password: str
    password_confirmation: str


class ChangePasswordBodyRequest(BaseModel):
    """
    Password change request body.

    Attributes:
        `code` (`str`):
            - Password change verification code.
        `new_password` (`str`):
            - New password.
        `new_password_confirmation` (`str`):
            - Confirmation of the new password.
    """

    code: str
    new_password: str
    new_password_confirmation: str


class ChangeEmailCodeBodyRequest(BaseModel):
    """
    Email change request body.

    Attributes:
        `new_email` (`EmailStr`):
            - New email address.
    """

    new_email: EmailStr
