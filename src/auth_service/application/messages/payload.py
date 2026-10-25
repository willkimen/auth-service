from dataclasses import asdict, dataclass
from typing import Protocol

from auth_service.application.messages.message_enums import MessageType


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

    @staticmethod
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

    @staticmethod
    def from_dict(data: dict) -> 'VerificationCodePayload':
        """Reconstructs the payload from a dictionary."""
        return VerificationCodePayload(**data)


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

    @staticmethod
    def from_dict(data: dict) -> 'NotificationPayload':
        """Reconstructs the payload from a dictionary."""
        return NotificationPayload(**data)


_PAYLOAD_TYPES: dict[MessageType, type[Payload]] = {
    MessageType.EMAIL_VERIFICATION_CODE: VerificationCodePayload,
    MessageType.NOTIFY_EMAIL_VERIFIED: NotificationPayload,
    MessageType.RESET_PASSWORD_CODE: VerificationCodePayload,
    MessageType.NOTIFY_PASSWORD_RESET: NotificationPayload,
    MessageType.CHANGE_PASSWORD_CODE: VerificationCodePayload,
    MessageType.NOTIFY_PASSWORD_CHANGED: NotificationPayload,
    MessageType.CHANGE_EMAIL_CODE: VerificationCodePayload,
    MessageType.NOTIFY_EMAIL_CHANGED: NotificationPayload,
    MessageType.ACCOUNT_DELETION_CODE: VerificationCodePayload,
    MessageType.NOTIFY_ACCOUNT_DELETED: NotificationPayload,
}


def payload_from_dict(
    message_type: MessageType,
    data: dict,
) -> Payload:
    """
    Reconstructs the appropriate payload for a message type.

    Args:
        message_type: Type identifying the message operation.
        data: Serialized payload data.

    Returns:
        Payload:
            The reconstructed payload instance.

    Raises:
        ValueError: If no payload implementation is registered
            for the specified message type.
    """
    payload_type = _PAYLOAD_TYPES.get(message_type)

    if payload_type is None:
        raise ValueError(
            f"No payload implementation registered for message type '{message_type}'"
        )

    return payload_type.from_dict(data)
