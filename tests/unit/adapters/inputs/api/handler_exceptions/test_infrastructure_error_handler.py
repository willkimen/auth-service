import json

from fastapi.responses import JSONResponse

import auth_service.application.exceptions as application_exceptions
from auth_service.adapters.inputs.api.handler_exceptions import (
    infrastructure_error_handler,
)


async def test_handles_infrastructure_error_correctly(fake_request):
    # arrange
    error = application_exceptions.InfrastructureError(
        message='',
        code=application_exceptions.InfrastructureErrorCode.DATABASE_ERROR,
        cause=Exception(),
    )
    expected_status_code = 500

    # act
    actual_response: JSONResponse = await infrastructure_error_handler(
        fake_request, error
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    assert json.loads(bytes(actual_response.body)) == {
        'error': {
            'code': 'INTERNAL_ERROR_SERVER',
            'message': 'internal error server',
        }
    }


async def test_handles_corrupted_persistence_error_correctly(fake_request):
    # arrange
    error = application_exceptions.CorruptedPersistenceStateError(
        cause=Exception(),
    )
    expected_status_code = 500

    # act
    actual_response: JSONResponse = await infrastructure_error_handler(
        fake_request, error
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    assert json.loads(bytes(actual_response.body)) == {
        'error': {
            'code': 'INTERNAL_ERROR_SERVER',
            'message': 'internal error server',
        }
    }
