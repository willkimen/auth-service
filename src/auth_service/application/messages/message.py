import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from auth_service.application.messages.message_types import MessageType
from auth_service.application.messages.payload import Payload


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
        `created_at` (datetime):
            - Timestamp of when the message instance was initialized.
              Automatically generated in UTC if omitted.
        `expires_at` (datetime | None):
            - Timestamp after which the message is considered invalid.
              Defaults to `None`.
        `published_at` (datetime | None):
            - Timestamp of the successful message processing.
              Defaults to `None`.
        `publish_attempts` (int):
            - Counter for the number of processing attempts made.
              Defaults to `0`.
        `id` (uuid.UUID):
            - Unique identifier for the message instance.
              Automatically generated via UUIDv4 if omitted.
    """

    type: MessageType
    payload: Payload
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    published_at: datetime | None = None
    publish_attempts: int = 0
    id: uuid.UUID = field(default_factory=uuid.uuid4)
