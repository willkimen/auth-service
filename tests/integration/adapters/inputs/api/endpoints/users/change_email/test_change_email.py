from httpx2 import AsyncClient

from auth_service.adapters.inputs.api.dependencies.use_cases import (
    change_email_factory,
)
from auth_service.application.exceptions import (
    CorruptedPersistenceStateError,
    EmailAlreadyUsedError,
)
from auth_service.domain.entities.user import User
from auth_service.domain.enums import CodeType
from auth_service.domain.exceptions import InactiveUserError, UserErrorCode

body_dummy = {'code': '123456'}


async def test_return_correctly_status_code(
    async_client: AsyncClient,
    clean_database: None,
    get_settings_override: None,
    create_access_token: str,
    persist_verified_user: User,
    persist_unused_verification_code,
):
    # arrange
    verification_code = await persist_unused_verification_code(
        persist_verified_user,
        CodeType.CHANGE_EMAIL,
        {'new_email': 'newemail@email.com'},
    )
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {create_access_token}',
    }
    body = {'code': verification_code.code.value}
    expected_status_code = 204

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/change',
        headers=headers,
        json=body,
    )

    # asserts
    assert actual_response.status_code == expected_status_code


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
    use_case_override_with_error(change_email_factory, Exception())
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/change',
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
        change_email_factory,
        InactiveUserError(),
    )
    expected_status_code = 403

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/change',
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
    use_case_override_with_error(change_email_factory, CorruptedPersistenceStateError())
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/change',
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
        change_email_factory,
        EmailAlreadyUsedError(),
    )
    expected_status_code = 409

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/change',
        headers=headers,
        json=body_dummy,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()['error']
    assert response_data['code'] == 'EMAIL_ALREADY_USE'
    assert response_data['message'] == ('An account with this email already exists')
