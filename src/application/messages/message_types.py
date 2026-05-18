from enum import StrEnum, auto


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
    NOTIFICATION_EMAIL_VERIFIED = auto()

    PASSWORD_RESET_CODE = auto()
    NOTIFICATION_PASSWORD_RESET = auto()

    PASSWORD_CHANGE_CODE = auto()
    NOTIFICATION_PASSWORD_CHANGED = auto()

    EMAIL_CHANGE_CODE = auto()
    NOTIFICATION_EMAIL_CHANGED = auto()

    DELETE_CODE = auto()
    NOTIFICATION_DELETED = auto()
