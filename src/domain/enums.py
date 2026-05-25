from enum import StrEnum, auto


class CodeType(StrEnum):
    """Defines the types of verification codes.

    Used to represent the purpose of a verification code.

    Attributes:
        `EMAIL_VERIFICATION` (str):
            - Used for initial user account email verification.
        `CHANGE_EMAIL` (str):
            - Used to authorize changing the current email address.
        `CHANGE_PASSWORD` (str):
            - Used to authorize password updates while authenticated.
        `RESET_PASSWORD` (str):
            - Used for password recovery when unauthenticated.
        `DELETE_ACCOUNT` (str):
            - Used to confirm and authorize permanent account closure.
    """

    EMAIL_VERIFICATION = auto()
    CHANGE_EMAIL = auto()
    CHANGE_PASSWORD = auto()
    RESET_PASSWORD = auto()
    DELETE_ACCOUNT = auto()
