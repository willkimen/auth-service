from enum import auto, StrEnum


class CodeType(StrEnum):
    """Defines the types of verification codes.

    Used to represent the purpose of a verification code.
    """

    EMAIL_VERIFICATION = auto()
    CHANGE_EMAIL = auto()
    CHANGE_PASSWORD = auto()
    RESET_PASSWORD = auto()
    DELETE_ACCOUNT = auto()
