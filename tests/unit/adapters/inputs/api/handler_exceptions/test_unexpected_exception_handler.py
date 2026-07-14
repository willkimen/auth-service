import json

from fastapi.responses import JSONResponse

from adapters.inputs.api.handler_exceptions import unexpected_exception_handler


async def test_handles_unexpected_error_correctly(fake_request):
    # arrange
    error = Exception()
    expected_status_code = 500

    # act
    actual_response: JSONResponse = await unexpected_exception_handler(
        fake_request, error
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    assert json.loads(bytes(actual_response.body)) == {
        'error': 'internal error server'
    }
