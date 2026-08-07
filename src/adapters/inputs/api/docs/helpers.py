from adapters.inputs.api.schemas import ErrorResponse
from application.exceptions import ApplicationError
from domain.exceptions import DomainError


def error_example(name: str, exc: DomainError | ApplicationError):
    return {
        'summary': name,
        'value': {
            'error': {
                'code': exc.code,
                'message': exc.message,
            }
        },
    }


INTERNAL_SERVER_ERROR_EXAMPLE = {
    'summary': 'Internal server error',
    'value': {
        'error': {
            'code': 'INTERNAL_ERROR_SERVER',
            'message': 'internal error server',
        }
    },
}

INTERNAL_SERVER_ERROR_RESPONSE = {
    'model': ErrorResponse,
    'description': 'An unexpected server error occurred.',
    'content': {
        'application/json': {
            'examples': {
                'internal_server_error': INTERNAL_SERVER_ERROR_EXAMPLE,
            }
        }
    },
}
