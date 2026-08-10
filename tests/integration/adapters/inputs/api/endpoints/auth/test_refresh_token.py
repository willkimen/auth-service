from httpx2 import AsyncClient

from auth_service.adapters.inputs.api.dependencies.use_cases import (
    refresh_factory,
)
from auth_service.application.exceptions import (
    CorruptedPersistenceStateError,
    EmailAlreadyUsedError,
)
from auth_service.domain.exceptions import InactiveUserError, UserErrorCode

body_dummy = {'refresh': 'refresh.dummy'}

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


async def test_return_correctly_response_data(
    async_client: AsyncClient,
    clean_database: None,
    get_settings_override: None,
    create_refresh_token: str,
    persist_valid_refresh_token: None,
):
    # arrange
    expected_status_code = 200
    body = {
        'refresh': create_refresh_token,
    }

    # act
    response = await async_client.post(
        '/api/v1/auth/token/refresh',
        headers=headers,
        json=body,
    )

    # asserts
    response_data = response.json()

    assert response.status_code == expected_status_code
    assert 'access' in response_data


async def test_should_handle_unexpected_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    use_case_override_with_error(refresh_factory, Exception())
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        '/api/v1/auth/token/refresh',
        headers=headers,
        json=body_dummy,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()['error']
    assert response_data['code'] == 'INTERNAL_ERROR_SERVER'
    assert response_data['message'] == 'internal error server'


async def test_should_handle_domain_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    use_case_override_with_error(refresh_factory, InactiveUserError())
    expected_status_code = 403

    # act
    actual_response = await async_client.post(
        '/api/v1/auth/token/refresh',
        headers=headers,
        json=body_dummy,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()['error']
    assert response_data['code'] == UserErrorCode.INACTIVE_USER
    assert response_data['message'] == 'User account is inactive'


async def test_should_handle_corrupted_persistence_state_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    use_case_override_with_error(refresh_factory, CorruptedPersistenceStateError())
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        '/api/v1/auth/token/refresh',
        headers=headers,
        json=body_dummy,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()['error']
    assert response_data['code'] == 'INTERNAL_ERROR_SERVER'
    assert response_data['message'] == 'internal error server'


async def test_should_handle_application_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    use_case_override_with_error(refresh_factory, EmailAlreadyUsedError())
    expected_status_code = 409

    # act
    actual_response = await async_client.post(
        '/api/v1/auth/token/refresh',
        headers=headers,
        json=body_dummy,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()['error']
    assert response_data['code'] == 'EMAIL_ALREADY_USE'
    assert response_data['message'] == ('An account with this email already exists')
