from dataclasses import asdict, dataclass, field
from typing import Protocol


class EmailPayload(Protocol):
    """Defines the contract for email payload objects.

    Used as payload data for integration events related to
    email sending.
    """

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        ...


# --- ACCOUNT VERIFICATION ---


@dataclass(slots=True, frozen=True)
class EmailVerificationPayload:
    """
    Data container for account activation emails.

    Attributes:
        to (str): Recipient's email address (e.g., "user@example.com").
        code (str): The numeric verification code (e.g., "123456").
        expiration (str): Time duration until the code expires.
            Expected: numeric string (e.g., "15").
        link (str): URL of the web page where the user must enter the code.
        deadline (str): Total days the user has to complete the verification.
            Expected: numeric string (e.g., "7").
        subject (str): Immutable email subject line.
    """

    to: str
    code: str
    expiration: str
    link: str
    deadline: str
    subject: str = field(default='Verify your email', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary for integration events.

        This method applies formatting to time-based fields:
        - 'deadline': Appends ' days' to the numeric string for
           template readability.
        - 'expiration': Appends ' minutes' to the numeric
           string to clarify duration.
        """
        data = asdict(self)
        data['deadline'] = f'{self.deadline} days'
        data['expiration'] = f'{self.expiration} minutes'
        return data


@dataclass(slots=True, frozen=True)
class EmailVerifiedPayload:
    """
    Data container for email verification confirmation.

    Attributes:
        to (str): Recipient's email address (e.g., "user@example.com").
        link (str): URL redirecting the user to the login page now that
            their account is active.
        subject (str): Immutable email subject line confirming success.
    """

    to: str
    link: str
    subject: str = field(default='Email verified successfully', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary.

        This dictionary is used to populate the email template
        with the user's information and the direct login link.
        """
        return asdict(self)


# --- EMAIL CHANGE ---


@dataclass(slots=True, frozen=True)
class ChangeEmailPayload:
    """
    Security payload for authorizing an email address change.

    Attributes:
        to (str): The new email address where the security code
            will be sent (e.g., "user@example.com").
        code (str): The verification code required to confirm the
            ownership of the new email (e.g., "987654").
        expiration (str): Duration until the authorization code expires.
            Expected: numeric string (e.g., "10").
        subject (str): Immutable email subject line for security authorization.
    """

    to: str
    code: str
    expiration: str
    subject: str = field(default='Confirm your email change', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary for integration events.

        The 'expiration' field is transformed from a numeric string
        to a user-friendly format by appending ' minutes'.
        """
        data = asdict(self)
        data['expiration'] = f'{self.expiration} minutes'
        return data


@dataclass(slots=True, frozen=True)
class EmailChangedPayload:
    """
    Final notification sent when an email update is successfully completed.

    Attributes:
        to (str): The new confirmed email address of the user
            (e.g., "new@example.com").
        link (str): URL for the login page, allowing the user to access the
            system with their new credentials.
        subject (str): Immutable email subject line notifying the change.
    """

    to: str
    link: str
    subject: str = field(default='Your email has been changed', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary.
        The resulting dictionary provides the template with the new email
        address and the link to the login screen.
        """
        return asdict(self)


# --- PASSWORD CHANGE ---


@dataclass(slots=True, frozen=True)
class ChangePasswordPayload:
    """
    Security code to authorize a password update for an active session.

    Attributes:
        to (str): User's email address (e.g., "user@example.com").
        code (str): The numeric authorization code (e.g., "456123").
        expiration (str): Minutes until code expires. Expected: "15".
        subject (str): Immutable email subject for security verification.
    """

    to: str
    code: str
    expiration: str
    subject: str = field(
        default='Security code for password change', init=False
    )

    def to_dict(self) -> dict:
        """
        Serializes payload to dict and appends ' minutes' to expiration.
        """
        data = asdict(self)
        data['expiration'] = f'{self.expiration} minutes'
        return data


@dataclass(slots=True, frozen=True)
class PasswordChangedPayload:
    """
    Security alert confirming that the account password was updated.

    Attributes:
        to (str): User's email address (e.g., "user@example.com").
        link (str): URL to the login page.
        subject (str): Immutable email subject line for security alert.
    """

    to: str
    link: str
    subject: str = field(default='Your password was changed', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary for the email event.
        """
        return asdict(self)


# --- PASSWORD RESET ---


@dataclass(slots=True, frozen=True)
class ResetPasswordPayload:
    """
    Data for the 'Forgot Password' flow to recover account access.

    Attributes:
        to (str): User's email address (e.g., "user@example.com").
        code (str): The recovery code to verify identity (e.g., "789012").
        expiration (str): Minutes until code expires. Expected: "20".
        link (str): URL of the page where the user sets the new password.
        subject (str): Immutable email subject for password recovery.
    """

    to: str
    code: str
    expiration: str
    link: str
    subject: str = field(default='Reset your password', init=False)

    def to_dict(self) -> dict:
        """
        Serializes payload and appends ' minutes' to the expiration field.
        """
        data = asdict(self)
        data['expiration'] = f'{self.expiration} minutes'
        return data


@dataclass(slots=True, frozen=True)
class PasswordResetPayload:
    """
    Final confirmation sent after a successful password recovery reset.

    Attributes:
        to (str): User's email address (e.g., "user@example.com").
        link (str): URL to the login page so the user can access their
            account with the new password.
        subject (str): Immutable email subject line for recovery success.
    """

    to: str
    link: str
    subject: str = field(default='Your password has been reset', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary for the email event.
        """
        return asdict(self)


# --- ACCOUNT DELETION ---


@dataclass(slots=True, frozen=True)
class DeleteAccountPayload:
    """
    Security challenge to confirm permanent account deletion.

    Attributes:
        to (str): User's email address (e.g., "user@example.com").
        code (str): The numeric code to authorize deletion (e.g., "321654").
        expiration (str): Minutes until code expires. Expected: "10".
        subject (str): Immutable email subject for deletion confirmation.
    """

    to: str
    code: str
    expiration: str
    subject: str = field(default='Confirm account deletion', init=False)

    def to_dict(self) -> dict:
        """
        Serializes payload and appends ' minutes' to the expiration field.
        """
        data = asdict(self)
        data['expiration'] = f'{self.expiration} minutes'
        return data


@dataclass(slots=True, frozen=True)
class AccountDeletedPayload:
    """
    Final notification sent after account and data are permanently removed.

    Attributes:
        to (str): User's email address (e.g., "user@example.com").
        subject (str): Immutable email subject for account closure.
    """

    to: str
    subject: str = field(default='Your account has been deleted', init=False)

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary for the email event.
        """
        return asdict(self)
