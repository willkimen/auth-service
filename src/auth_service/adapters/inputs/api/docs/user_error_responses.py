from fastapi import status

from auth_service.adapters.inputs.api.docs.application_error_examples import (
    EMAIL_ALREADY_USED_EXAMPLES,
    INVALID_TOKEN_EXAMPLES,
    INVALID_TOKEN_TYPE_EXAMPLES,
    PASSWORD_MISMATCH_EXAMPLES,
    USER_NOT_FOUND_EXAMPLES,
    VERIFICATION_CODE_NOT_FOUND_EXAMPLES,
)
from auth_service.adapters.inputs.api.docs.domain_error_examples import (
    EMAIL_ALREADY_VERIFIED_EXAMPLES,
    INACTIVE_USER_EXAMPLES,
    INVALID_EMAIL_EXAMPLES,
    INVALID_PASSWORD_EXAMPLES,
    VERIFICATION_CODE_ALREADY_USED_EXAMPLES,
    VERIFICATION_CODE_EXPIRED_EXAMPLES,
    VERIFICATION_CODE_TYPE_EXAMPLES,
)
from auth_service.adapters.inputs.api.docs.helpers import (
    INTERNAL_SERVER_ERROR_RESPONSE,
)
from auth_service.adapters.inputs.api.schemas import ErrorResponse

change_email_code_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': (
            'The request contains invalid data or the token type '
            'is not valid for this operation.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_EMAIL_EXAMPLES,
                    **INVALID_TOKEN_TYPE_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': ('The access token is invalid or authentication failed.'),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': ('The authenticated user cannot perform this operation.'),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The authenticated user was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


change_email_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': (
            'The request contains invalid data or the verification '
            'code type is not valid for this operation.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_TYPE_EXAMPLES,
                    **VERIFICATION_CODE_TYPE_EXAMPLES,
                    **INVALID_EMAIL_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'The access token is invalid, expired, malformed, or cannot be decoded.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': ('The authenticated user cannot perform this operation.'),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The requested user or verification code was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                    **VERIFICATION_CODE_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_409_CONFLICT: {
        'model': ErrorResponse,
        'description': ('The verification code has already been used.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_ALREADY_USED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_410_GONE: {
        'model': ErrorResponse,
        'description': ('The verification code has expired.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_EXPIRED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


change_password_code_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': (
            'The request contains an invalid token type for this operation.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_TYPE_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'The access token is invalid, expired, malformed, '
            'or contains invalid claims.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': ('The authenticated user cannot perform this operation.'),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The authenticated user was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


change_password_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': (
            'The request contains invalid data, password validation '
            'failed, or the verification code/token type is invalid.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_PASSWORD_EXAMPLES,
                    **PASSWORD_MISMATCH_EXAMPLES,
                    **INVALID_TOKEN_TYPE_EXAMPLES,
                    **VERIFICATION_CODE_TYPE_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'The access token is invalid, expired, malformed, or cannot be validated.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': ('The authenticated user cannot perform this operation.'),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The authenticated user or verification code was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                    **VERIFICATION_CODE_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_409_CONFLICT: {
        'model': ErrorResponse,
        'description': ('The verification code has already been used.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_ALREADY_USED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_410_GONE: {
        'model': ErrorResponse,
        'description': ('The verification code has expired.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_EXPIRED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}

detail_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': (
            'The request contains an invalid token type for this operation.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_TYPE_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'The access token is invalid, expired, malformed, or cannot be validated.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': ('The authenticated user cannot access this resource.'),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The authenticated user was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}

register_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': (
            'The request contains invalid data or does not satisfy '
            'the validation rules.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_EMAIL_EXAMPLES,
                    **INVALID_PASSWORD_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_409_CONFLICT: {
        'model': ErrorResponse,
        'description': (
            'The email address is already associated with another account.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **EMAIL_ALREADY_USED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


delete_account_code_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': ('The provided token type is invalid for this operation.'),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_TYPE_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'The access token is invalid, expired, malformed, '
            'or contains invalid claims.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': (
            'The authenticated user cannot perform this operation '
            'because the account is inactive.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The authenticated user was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


delete_account_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': (
            'The request contains an invalid token type or verification code type.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_TYPE_EXAMPLES,
                    **VERIFICATION_CODE_TYPE_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': (
            'The access token is invalid, expired, malformed, or cannot be validated.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': (
            'The authenticated user cannot perform this operation '
            'because the account is inactive.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The authenticated user or verification code was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                    **VERIFICATION_CODE_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_409_CONFLICT: {
        'model': ErrorResponse,
        'description': ('The verification code has already been used.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_ALREADY_USED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_410_GONE: {
        'model': ErrorResponse,
        'description': ('The verification code has expired.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_EXPIRED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


email_verification_code_responses = {
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': (
            'The user account cannot start the email verification '
            'process because it is inactive.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('No user was found with the provided email address.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_409_CONFLICT: {
        'model': ErrorResponse,
        'description': ('The user email has already been verified.'),
        'content': {
            'application/json': {
                'examples': {
                    **EMAIL_ALREADY_VERIFIED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}

email_verification_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': ('The verification code type is invalid for this operation.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_TYPE_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': (
            'The user account cannot complete email verification '
            'because it is inactive.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The requested user or verification code was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                    **VERIFICATION_CODE_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_409_CONFLICT: {
        'model': ErrorResponse,
        'description': (
            'The email is already verified or the verification code '
            'has already been used.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **EMAIL_ALREADY_VERIFIED_EXAMPLES,
                    **VERIFICATION_CODE_ALREADY_USED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_410_GONE: {
        'model': ErrorResponse,
        'description': ('The verification code has expired.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_EXPIRED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


reset_password_code_responses = {
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': (
            'The user account cannot start the password reset '
            'process because it is inactive.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('No user was found with the provided email address.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}

reset_password_responses = {
    status.HTTP_400_BAD_REQUEST: {
        'model': ErrorResponse,
        'description': (
            'The request contains invalid password data or the '
            'verification code type is incorrect.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_PASSWORD_EXAMPLES,
                    **PASSWORD_MISMATCH_EXAMPLES,
                    **VERIFICATION_CODE_TYPE_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': (
            'The user account cannot reset the password because it is inactive.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_404_NOT_FOUND: {
        'model': ErrorResponse,
        'description': ('The requested user or verification code was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **USER_NOT_FOUND_EXAMPLES,
                    **VERIFICATION_CODE_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_409_CONFLICT: {
        'model': ErrorResponse,
        'description': ('The verification code has already been used.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_ALREADY_USED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_410_GONE: {
        'model': ErrorResponse,
        'description': ('The verification code has expired.'),
        'content': {
            'application/json': {
                'examples': {
                    **VERIFICATION_CODE_EXPIRED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}
