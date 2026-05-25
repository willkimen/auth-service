import uuid
from dataclasses import dataclass, field

from application.messages.message_types import MessageType
from application.messages.payload import Payload


@dataclass(slots=True)
class Message:
    """
    Represents a message registered for processing.

    A message encapsulates the information required by a
    message handler to execute a specific operation.

    Messages are typically persisted and later consumed
    by dedicated processing components.

    Attributes:
        `type` (MessageType):
            - The specific message type to be processed.
        `payload` (Payload):
            - The payload containing the data required
              for message processing.
        `id` (uuid.UUID):
            - Unique identifier for the message instance.
              Automatically generated when omitted.
    """

    type: MessageType
    payload: Payload
    id: uuid.UUID = field(default_factory=uuid.uuid4)
