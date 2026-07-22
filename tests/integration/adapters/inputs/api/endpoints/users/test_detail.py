from datetime import datetime

from httpx2 import AsyncClient

from adapters.inputs.api.dependencies.use_cases import (
    detail_factory,
)
from application.exceptions import (
    CorruptedPersistenceStateError,
    EmailAlreadyUsedError,
)
from domain.entities.user import User
from domain.exceptions import InactiveUserError, UserErrorCode


async def test_return_correctly_response_data(
    async_client: AsyncClient,
    clean_database: None,
    get_settings_override: None,
    persist_verified_user: User,
    create_access_token: str,
):
    # arrange
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {create_access_token}',
    }
    expected_status_code = 200

    # act
    actual_response = await async_client.get(
        '/api/v1/users/detail',
        headers=headers,
    )

    # asserts
    response_data = actual_response.json()

    assert actual_response.status_code == expected_status_code
    assert response_data['public_id'] == str(persist_verified_user.public_id)
    assert response_data['email'] == persist_verified_user.email.value
    assert (
        response_data['email_verified'] == persist_verified_user.email_verified
    )
    last_login_at_dt = datetime.fromisoformat(
        response_data['last_login_at'].replace('Z', '+00:00')
    )
    assert last_login_at_dt == persist_verified_user.last_login_at

    created_at_dt = datetime.fromisoformat(
        response_data['created_at'].replace('Z', '+00:00')
    )
    assert created_at_dt == persist_verified_user.created_at

    assert 'password' not in response_data


async def test_should_handle_unexpected_exception(
    async_client: AsyncClient,
    clean_database: None,
    use_case_override_with_error,
    create_access_token: str,
):
    # arrange
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {create_access_token}',
    }
    use_case_override_with_error(detail_factory, Exception())
    expected_status_code = 500

    # act
    actual_response = await async_client.get(
        '/api/v1/users/detail',
        headers=headers,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()
    assert response_data['error'] == 'internal error server'


async def test_should_handle_domain_exception(
    async_client: AsyncClient,
    clean_database: None,
    use_case_override_with_error,
    create_access_token: str,
):
    # arrange
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {create_access_token}',
    }
    use_case_override_with_error(detail_factory, InactiveUserError())
    expected_status_code = 403

    # act
    actual_response = await async_client.get(
        '/api/v1/users/detail',
        headers=headers,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()['error']
    assert response_data['code'] == UserErrorCode.INACTIVE_USER
    assert response_data['message'] == 'User account is inactive'


async def test_should_handle_corrupted_persistence_state_exception(
    async_client: AsyncClient,
    clean_database: None,
    use_case_override_with_error,
    create_access_token: str,
):
    # arrange
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {create_access_token}',
    }
    use_case_override_with_error(
        detail_factory, CorruptedPersistenceStateError()
    )
    expected_status_code = 500

    # act
    actual_response = await async_client.get(
        '/api/v1/users/detail',
        headers=headers,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()
    assert response_data['error'] == 'internal error server'


async def test_should_handle_application_exception(
    async_client: AsyncClient,
    clean_database: None,
    use_case_override_with_error,
    create_access_token: str,
):
    # arrange
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {create_access_token}',
    }
    use_case_override_with_error(detail_factory, EmailAlreadyUsedError())
    expected_status_code = 409

    # act
    actual_response = await async_client.get(
        '/api/v1/users/detail',
        headers=headers,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()['error']
    assert response_data['code'] == 'EMAIL_ALREADY_USE'
    assert response_data['message'] == (
        'An account with this email already exists'
    )
