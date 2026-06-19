from dataclasses import asdict, dataclass, field

# --- ACCOUNT VERIFICATION ---


@dataclass(slots=True, frozen=True)
class EmailVerificationPayload:
    """
    Data container for account activation emails.

    Attributes:
        `to` (str):
            - Recipient's email address (e.g., "user@example.com").
        `code` (str):
            - The numeric verification code (e.g., "123456").
        `subject` (str):
            - Immutable email subject line.
    """

    to: str
    code: str
    subject: str = field(default='Verify your email', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary.
        """
        return asdict(self)


@dataclass(slots=True, frozen=True)
class EmailVerifiedPayload:
    """
    Data container for email verification confirmation.

    Attributes:
        `to` (str):
            - Recipient's email address (e.g., "user@example.com").
        `subject` (str):
            - Immutable email subject line confirming success.
    """

    to: str
    subject: str = field(default='Email verified successfully', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary.
        """
        return asdict(self)


# --- EMAIL CHANGE ---


@dataclass(slots=True, frozen=True)
class ChangeEmailPayload:
    """
    Security payload for authorizing an email address change.

    Attributes:
        `to` (str):
            - The new email address where the security code
              will be sent (e.g., "user@example.com").
        `code` (str):
            - The verification code required to confirm the
              ownership of the new email (e.g., "987654").
        `subject` (str):
            - Immutable email subject line for security
              authorization.
    """

    to: str
    code: str
    subject: str = field(default='Confirm your email change', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary.
        """
        return asdict(self)


@dataclass(slots=True, frozen=True)
class EmailChangedPayload:
    """
    Final notification sent when an email update is successfully completed.

    Attributes:
        `to` (str):
            - The new confirmed email address of the user
              (e.g., "new@example.com").
        `subject` (str):
            - Immutable email subject line notifying the change.
    """

    to: str
    subject: str = field(default='Your email has been changed', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary.
        """
        return asdict(self)


# --- PASSWORD CHANGE ---


@dataclass(slots=True, frozen=True)
class ChangePasswordPayload:
    """
    Security code to authorize a password update for an active session.

    Attributes:
        `to` (str):
            - User's email address (e.g., "user@example.com").
        `code` (str):
            - The numeric authorization code (e.g., "456123").
        `subject` (str):
            - Immutable email subject for security verification.
    """

    to: str
    code: str
    subject: str = field(
        default='Security code for password change', init=False
    )

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary.
        """
        return asdict(self)


@dataclass(slots=True, frozen=True)
class PasswordChangedPayload:
    """
    Security alert confirming that the account password was updated.

    Attributes:
        `to` (str):
            - User's email address (e.g., "user@example.com").
        `subject` (str):
            - Immutable email subject line for security alert.
    """

    to: str
    subject: str = field(default='Your password was changed', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary.
        """
        return asdict(self)


# --- PASSWORD RESET ---


@dataclass(slots=True, frozen=True)
class ResetPasswordPayload:
    """
    Data for the 'Forgot Password' flow to recover account access.

    Attributes:
        `to` (str):
            - User's email address (e.g., "user@example.com").
        `code` (str):
            - The recovery code to verify identity (e.g., "789012").
        `subject` (str):
            - Immutable email subject for password recovery.
    """

    to: str
    code: str
    subject: str = field(default='Reset your password', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary.
        """
        return asdict(self)


@dataclass(slots=True, frozen=True)
class PasswordResetPayload:
    """
    Final confirmation sent after a successful password recovery reset.

    Attributes:
        `to` (str):
            - User's email address (e.g., "user@example.com").
        `subject` (str):
            - Immutable email subject line for recovery success.
    """

    to: str
    subject: str = field(default='Your password has been reset', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary.
        """
        return asdict(self)


# --- ACCOUNT DELETION ---


@dataclass(slots=True, frozen=True)
class DeleteAccountPayload:
    """
    Security challenge to confirm permanent account deletion.

    Attributes:
        `to` (str):
            - User's email address (e.g., "user@example.com").
        `code` (str):
            - The numeric code to authorize deletion (e.g., "321654").
        `subject` (str):
            - Immutable email subject for deletion confirmation.
    """

    to: str
    code: str
    subject: str = field(default='Confirm account deletion', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary.
        """
        return asdict(self)


@dataclass(slots=True, frozen=True)
class AccountDeletedPayload:
    """
    Final notification sent after account and data are permanently removed.

    Attributes:
        `to` (str):
            - User's email address (e.g., "user@example.com").
        `subject` (str):
            - Immutable email subject for account closure.
    """

    to: str
    subject: str = field(default='Your account has been deleted', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary.
        """
        return asdict(self)
