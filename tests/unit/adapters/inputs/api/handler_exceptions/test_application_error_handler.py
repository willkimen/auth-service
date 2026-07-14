import json

from fastapi.responses import JSONResponse

import application.exceptions as application_exceptions
from adapters.inputs.api.handler_exceptions import application_error_handler


async def test_handles_application_error_correctly(fake_request):
    # arrange
    error = application_exceptions.EmailAlreadyUsedError()
    expected_status_code = 409

    # act
    actual_response: JSONResponse = await application_error_handler(
        fake_request, error
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    assert json.loads(bytes(actual_response.body)) == {
        'error': {
            'code': error.code,
            'message': error.message,
        }
    }
