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


class VerificationCodePayload:
    """Payload for account verification emails."""

    def __init__(
        self,
        to: str,
        verification_code: str,
        code_expiration_time: str,
        email_verification_link: str,
        email_verification_deadline_days: int,
    ):
        self.to = to
        self.verification_code = verification_code
        self.code_expiration_time = code_expiration_time
        self.email_verification_link = email_verification_link
        self.email_verification_deadline_days = (
            email_verification_deadline_days
        )

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'verification_code': self.verification_code,
            'code_expiration_time': self.code_expiration_time,
            'email_verification_link': self.email_verification_link,
            'email_verification_deadline_days': (
                self.email_verification_deadline_days,
            ),
        }


class NotifyEmailVerifiedPayload:
    """Payload for email verification confirmation emails."""

    def __init__(self, to: str, login_link: str):
        self.to = to
        self.login_link = login_link

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'login_link': self.login_link,
        }


class ChangeEmailCodePayload:
    """Payload for email change verification emails."""

    def __init__(
        self,
        to: str,
        verification_code: str,
        code_expiration_time: str,
    ):
        self.to = to
        self.verification_code = verification_code
        self.code_expiration_time = code_expiration_time

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'verification_code': self.verification_code,
            'code_expiration_time': self.code_expiration_time,
        }


class NotifyChangeEmailPayload:
    """Payload for email change confirmation emails."""

    def __init__(self, to: str, login_link: str):
        self.to = to
        self.login_link = login_link

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'login_link': self.login_link,
        }


class ChangePasswordCodePayload:
    """Payload for password change verification emails."""

    def __init__(
        self,
        to: str,
        verification_code: str,
        code_expiration_time: str,
    ):
        self.to = to
        self.verification_code = verification_code
        self.code_expiration_time = code_expiration_time

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'verification_code': self.verification_code,
            'code_expiration_time': self.code_expiration_time,
        }


class NotifyChangePasswordPayload:
    """Payload for password change confirmation emails."""

    def __init__(self, to: str, login_link: str):
        self.to = to
        self.login_link = login_link

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'login_link': self.login_link,
        }


class ResetPasswordCodePayload:
    """Payload for password reset emails."""

    def __init__(
        self,
        to: str,
        verification_code: str,
        code_expiration_time: str,
        reset_password_link: str,
    ):
        self.to = to
        self.verification_code = verification_code
        self.code_expiration_time = code_expiration_time
        self.reset_password_link = reset_password_link

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'verification_code': self.verification_code,
            'code_expiration_time': self.code_expiration_time,
            'reset_password_link': self.reset_password_link,
        }


class NotifyResetPasswordPayload:
    """Payload for password reset confirmation emails."""

    def __init__(self, to: str, login_link: str):
        self.to = to
        self.login_link = login_link

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'login_link': self.login_link,
        }


class DeletionCodePayload:
    """Payload for account deletion verification emails."""

    def __init__(
        self,
        to: str,
        verification_code: str,
        code_expiration_time: str,
    ):
        self.to = to
        self.verification_code = verification_code
        self.code_expiration_time = code_expiration_time

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
            'verification_code': self.verification_code,
            'code_expiration_time': self.code_expiration_time,
        }


class NotifyDeletionPayload:
    """Payload for account deletion confirmation emails."""

    def __init__(self, to: str):
        self.to = to

    def to_dict(self) -> dict:
        """Converts payload into serializable dictionary.

        Returns:
            dict: Serialized payload data.
        """
        return {
            'to': self.to,
        }
