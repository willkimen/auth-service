from enum import Enum


class CodeType(str, Enum):
    """Defines the types of verification codes.

    Used to represent the purpose of a verification code.
    """

    EMAIL_VERIFICATION = 'EMAIL_VERIFICATION'
    CHANGE_EMAIL = 'CHANGE_EMAIL'
    CHANGE_PASSWORD = 'CHANGE_PASSWORD'
    RESET_PASSWORD = 'RESET_PASSWORD'
    DELETE_ACCOUNT = 'DELETE_ACCOUNT'
