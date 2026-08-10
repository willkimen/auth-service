from fastapi import status

from auth_service.adapters.inputs.api.docs.application_error_examples import (
    INVALID_CREDENTIALS_EXAMPLES,
    INVALID_TOKEN_EXAMPLES,
    INVALID_TOKEN_TYPE_EXAMPLES,
    TOKEN_NOT_FOUND_EXAMPLES,
    TOKEN_REVOKED_EXAMPLES,
    USER_NOT_FOUND_EXAMPLES,
)
from auth_service.adapters.inputs.api.docs.domain_error_examples import (
    INACTIVE_USER_EXAMPLES,
    UNVERIFIED_EMAIL_EXAMPLES,
)
from auth_service.adapters.inputs.api.docs.helpers import (
    INTERNAL_SERVER_ERROR_RESPONSE,
)
from auth_service.adapters.inputs.api.schemas import ErrorResponse

login_responses = {
    status.HTTP_401_UNAUTHORIZED: {
        'model': ErrorResponse,
        'description': ('The provided credentials are invalid.'),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_CREDENTIALS_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': (
            'The user account cannot authenticate because it is '
            'inactive or the email has not been verified.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INACTIVE_USER_EXAMPLES,
                    **UNVERIFIED_EMAIL_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


refresh_token_responses = {
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
            'The refresh token is invalid, expired, malformed, or has been revoked.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                    **TOKEN_REVOKED_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_403_FORBIDDEN: {
        'model': ErrorResponse,
        'description': (
            'The authenticated user cannot refresh the token '
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
        'description': ('The refresh token or authenticated user was not found.'),
        'content': {
            'application/json': {
                'examples': {
                    **TOKEN_NOT_FOUND_EXAMPLES,
                    **USER_NOT_FOUND_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}

revoke_all_refreshes_responses = {
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
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}


revoke_refresh_responses = {
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
            'The refresh token is invalid, expired, malformed, or cannot be validated.'
        ),
        'content': {
            'application/json': {
                'examples': {
                    **INVALID_TOKEN_EXAMPLES,
                }
            }
        },
    },
    status.HTTP_500_INTERNAL_SERVER_ERROR: INTERNAL_SERVER_ERROR_RESPONSE,
}
