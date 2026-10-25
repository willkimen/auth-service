from enum import StrEnum, auto


class MessageStatus(StrEnum):
    PENDING = 'pending'
    PUBLISHED = 'published'
    FAILED = 'failed'


class MessageFailureCode(StrEnum):
    BROKER_UNAVAILABLE = 'broker_unavailable'
    PUBLISH_TIMEOUT = 'publish_timeout'
    MESSAGE_UNROUTABLE = 'message_unroutable'
    PUBLISH_REJECTED = 'publish_rejected'
    SERIALIZATION_ERROR = 'serialization_error'
    UNKNOWN = 'unknown'


class MessageType(StrEnum):
    """
    Defines the supported message types.

    Each message type represents a specific operation
    intended to be executed later by a dedicated
    processing component.

    Message types are used to identify which handler
    or processing flow should handle a persisted message.
    """

    EMAIL_VERIFICATION_CODE = auto()
    NOTIFY_EMAIL_VERIFIED = auto()

    RESET_PASSWORD_CODE = auto()
    NOTIFY_PASSWORD_RESET = auto()

    CHANGE_PASSWORD_CODE = auto()
    NOTIFY_PASSWORD_CHANGED = auto()

    CHANGE_EMAIL_CODE = auto()
    NOTIFY_EMAIL_CHANGED = auto()

    ACCOUNT_DELETION_CODE = auto()
    NOTIFY_ACCOUNT_DELETED = auto()
