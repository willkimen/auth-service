import json

from fastapi.responses import JSONResponse

import domain.exceptions as domain_exceptions
from adapters.inputs.api.handler_exceptions import domain_error_handler


async def test_handles_domain_error_correctly(fake_request):
    # arrange
    error = domain_exceptions.EmailAlreadyVerifiedError(
        message='',
    )
    expected_status_code = 409

    # act
    actual_response: JSONResponse = await domain_error_handler(
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
