from fastapi import Request
from fastapi.responses import JSONResponse

import application.exceptions as application_exceptions
import domain.exceptions as domain_exceptions
from adapters.inputs.api.app import app


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
              error message.
    """
    return JSONResponse(
        status_code=500,
        content={
            'error': 'internal error server',
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
              error message.
    """
    return JSONResponse(
        status_code=500,
        content={
            'error': 'internal error server',
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
async def domain_error_handler(
    request: Request, exc: domain_exceptions.DomainError
):
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
        application_exceptions.PasswordMismatchError: 400,
        application_exceptions.InvalidTokenTypeError: 400,
        application_exceptions.InvalidTokenError: 401,
        application_exceptions.InvalidCredentialsError: 401,
        application_exceptions.TokenRevokedError: 401,
        application_exceptions.UserNotFoundError: 404,
        application_exceptions.VerificationCodeNotFoundError: 404,
        application_exceptions.TokenNotFoundError: 404,
        application_exceptions.EmailAlreadyUsedError: 409,
    }

    domain_exceptions_table = {
        domain_exceptions.InvalidPasswordError: 400,
        domain_exceptions.InvalidEmailError: 400,
        domain_exceptions.InvalidCodeError: 400,
        domain_exceptions.VerificationCodeTypeError: 400,
        domain_exceptions.MissingNewEmailError: 400,
        domain_exceptions.InactiveUserError: 403,
        domain_exceptions.UnverifiedEmailError: 403,
        domain_exceptions.EmailAlreadyVerifiedError: 409,
        domain_exceptions.VerificationCodeAlreadyUsedError: 409,
        domain_exceptions.VerificationCodeExpiredError: 410,
    }

    tables = {
        **domain_exceptions_table,
        **application_exceptions_table,
    }

    for exception_error, status_code in tables.items():
        if isinstance(exc, exception_error):
            return status_code

    return 500
