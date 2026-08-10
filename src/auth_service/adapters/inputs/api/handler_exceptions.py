from fastapi import Request, status
from fastapi.responses import JSONResponse

import auth_service.application.exceptions as application_exceptions
import auth_service.domain.exceptions as domain_exceptions
from auth_service.adapters.inputs.api.app import app


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception):
    """
    Handles unexpected exceptions that are not explicitly mapped to an
    application or domain exception handler.

    Args:
        `request` (`Request`):
            - Incoming HTTP request associated with the exception.
        `exc` (`Exception`):
            - Unexpected exception raised during request processing.

    Returns:
        `JSONResponse`:
            - HTTP 500 response containing a generic internal server
              error message and code.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'error': {
                'code': 'INTERNAL_ERROR_SERVER',
                'message': 'internal error server',
            }
        },
    )


@app.exception_handler(application_exceptions.InfrastructureError)
@app.exception_handler(application_exceptions.CorruptedPersistenceStateError)
async def infrastructure_error_handler(
    request: Request, exc: application_exceptions.InfrastructureError
):
    """
    Handles infrastructure-related and corrupted persistence errors.

    Args:
        `request` (`Request`):
            - Incoming HTTP request associated with the exception.
        `exc` (`InfrastructureError`):
            - Infrastructure or persistence error raised during request
              processing.

    Returns:
        `JSONResponse`:
            - HTTP 500 response containing a generic internal server
              error message and code.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'error': {
                'code': 'INTERNAL_ERROR_SERVER',
                'message': 'internal error server',
            }
        },
    )


@app.exception_handler(application_exceptions.ApplicationError)
async def application_error_handler(
    request: Request, exc: application_exceptions.ApplicationError
):
    """
    Handles application-layer exceptions and converts them into
    standardized HTTP error responses.

    Args:
        `request` (`Request`):
            - Incoming HTTP request associated with the exception.
        `exc` (`ApplicationError`):
            - Application-layer exception containing an error code
              and message.

    Returns:
        `JSONResponse`:
            - HTTP response containing the status code mapped to the
              application exception and its corresponding error details.
    """
    return JSONResponse(
        status_code=get_status_code(exc),
        content={
            'error': {
                'code': exc.code,
                'message': exc.message,
            }
        },
    )


@app.exception_handler(domain_exceptions.DomainError)
async def domain_error_handler(request: Request, exc: domain_exceptions.DomainError):
    """
    Handles domain-layer exceptions and converts them into standardized
    HTTP error responses.

    Args:
        `request` (`Request`):
            - Incoming HTTP request associated with the exception.
        `exc` (`DomainError`):
            - Domain-layer exception containing an error code and message.

    Returns:
        `JSONResponse`:
            - HTTP response containing the status code mapped to the
              domain exception and its corresponding error details.
    """
    return JSONResponse(
        status_code=get_status_code(exc),
        content={
            'error': {
                'code': exc.code,
                'message': exc.message,
            }
        },
    )


def get_status_code(exc: Exception) -> int:
    """
    Resolves the HTTP status code associated with an application or
    domain exception.

    Args:
        `exc` (`Exception`):
            - Exception whose type is used to determine the corresponding
              HTTP status code.

    Returns:
        `int`:
            - HTTP status code mapped to the exception type.
              Returns `500` when no explicit mapping exists.
    """
    application_exceptions_table = {
        application_exceptions.PasswordMismatchError: (status.HTTP_400_BAD_REQUEST),
        application_exceptions.InvalidTokenTypeError: (status.HTTP_400_BAD_REQUEST),
        application_exceptions.InvalidTokenError: (status.HTTP_401_UNAUTHORIZED),
        application_exceptions.InvalidCredentialsError: (status.HTTP_401_UNAUTHORIZED),
        application_exceptions.TokenRevokedError: (status.HTTP_401_UNAUTHORIZED),
        application_exceptions.UserNotFoundError: (status.HTTP_404_NOT_FOUND),
        application_exceptions.VerificationCodeNotFoundError: (
            status.HTTP_404_NOT_FOUND
        ),
        application_exceptions.TokenNotFoundError: (status.HTTP_404_NOT_FOUND),
        application_exceptions.EmailAlreadyUsedError: (status.HTTP_409_CONFLICT),
    }

    domain_exceptions_table = {
        domain_exceptions.InvalidPasswordError: (status.HTTP_400_BAD_REQUEST),
        domain_exceptions.InvalidEmailError: (status.HTTP_400_BAD_REQUEST),
        domain_exceptions.InvalidCodeError: (status.HTTP_400_BAD_REQUEST),
        domain_exceptions.VerificationCodeTypeError: (status.HTTP_400_BAD_REQUEST),
        domain_exceptions.MissingNewEmailError: (status.HTTP_400_BAD_REQUEST),
        domain_exceptions.InactiveUserError: (status.HTTP_403_FORBIDDEN),
        domain_exceptions.UnverifiedEmailError: (status.HTTP_403_FORBIDDEN),
        domain_exceptions.EmailAlreadyVerifiedError: (status.HTTP_409_CONFLICT),
        domain_exceptions.VerificationCodeAlreadyUsedError: (status.HTTP_409_CONFLICT),
        domain_exceptions.VerificationCodeExpiredError: (status.HTTP_410_GONE),
    }

    tables = {
        **domain_exceptions_table,
        **application_exceptions_table,
    }

    for exception_error, status_code in tables.items():
        if isinstance(exc, exception_error):
            return status_code

    return status.HTTP_500_INTERNAL_SERVER_ERROR
