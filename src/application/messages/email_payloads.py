from dataclasses import asdict, dataclass


@dataclass(slots=True, frozen=True)
class EmailCodePayload:
    """
    Class containing the data required to send
    an email with a verification code.

    Attributes:
        `to` (str):
            - Recipient's email address (e.g., "user@example.com").
        `code` (str):
            - The numeric verification code (e.g., "123456").
    """

    to: str
    code: str

    def to_dict(self) -> dict:
        """
        Serializes the payload to a dictionary.
        """
        return asdict(self)


@dataclass(slots=True, frozen=True)
class EmailNotificationPayload:
    """
    Class containing the data required to send a notification email.

    Attributes:
        `to` (str):
            - Recipient's email address (e.g., "user@example.com").
    """

    to: str

    def to_dict(self) -> dict:
        """
        Serializes the payload into a dictionary.
        """
        return asdict(self)
