from dataclasses import asdict, dataclass
from typing import Protocol


class Payload(Protocol):
    """
    Defines the contract for message payload objects.

    Payload objects encapsulate the data required by message
    handlers to process a specific message type.

    Implementations must provide a serializable representation
    so the payload can be persisted and reconstructed when
    the message is processed.
    """

    def to_dict(self) -> dict:
        """
        Converts the payload into a serializable dictionary.

        Returns:
            dict:
                Serialized payload data used during message
                persistence and processing.
        """
        ...

    def from_dict(data: dict) -> 'Payload':
        """
        Reconstructs a payload object from its serialized data.

        Args:
            data: Serialized payload data.

        Returns:
            Payload:
                A payload instance reconstructed from the data.
        """
        ...


@dataclass(slots=True, frozen=True)
class VerificationCodePayload:
    """
    Contains the data required to deliver a verification code.

    Attributes:
        recipient (str):
            Recipient identifier, such as an email address
            or phone number.
        code (str):
            Verification code.
    """

    recipient: str
    code: str

    def to_dict(self) -> dict:
        """Serializes the payload to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'VerificationCodePayload':
        """Reconstructs the payload from a dictionary."""
        return cls(**data)


@dataclass(slots=True, frozen=True)
class NotificationPayload:
    """
    Contains the data required to notify a recipient.

    Attributes:
        recipient (str):
            Recipient identifier.
    """

    recipient: str

    def to_dict(self) -> dict:
        """Serializes the payload to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'NotificationPayload':
        """Reconstructs the payload from a dictionary."""
        return cls(**data)
