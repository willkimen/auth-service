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

    SEND_EMAIL_VERIFICATION_CODE = auto()
    SEND_NOTIFICATION_EMAIL_VERIFIED = auto()

    SEND_PASSWORD_RESET_CODE = auto()
    SEND_NOTIFICATION_PASSWORD_RESET = auto()

    SEND_PASSWORD_CHANGE_CODE = auto()
    SEND_NOTIFICATION_PASSWORD_CHANGED = auto()

    SEND_EMAIL_CHANGE_CODE = auto()
    SEND_NOTIFICATION_EMAIL_CHANGED = auto()

    SEND_DELETE_CODE = auto()
    SEND_NOTIFICATION_DELETED = auto()
