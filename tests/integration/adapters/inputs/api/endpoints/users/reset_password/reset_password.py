from httpx2 import AsyncClient

from adapters.inputs.api.dependencies.use_cases import (
    reset_password_factory,
)
from application.exceptions import (
    CorruptedPersistenceStateError,
    EmailAlreadyUsedError,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.exceptions import InactiveUserError, UserErrorCode

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


async def test_return_correctly_status_code(
    async_client: AsyncClient,
    persist_unverified_user: User,
    persist_unused_verification_code: VerificationCode,
    get_settings_override: None,
    clean_database,
):
    # arrange
    expected_status_code = 204
    body = {
        'email': persist_unverified_user.email.value,
        'code': persist_unused_verification_code.code.value,
        'password': 'Password!1234',
        'password_confirmation': 'Password!1234',
    }

    # act
    response = await async_client.post(
        '/api/v1/users/password/reset',
        headers=headers,
        json=body,
    )

    # assert
    assert response.status_code == expected_status_code


async def test_should_handle_unexpected_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    body = {
        'email': 'email@email.com',
        'code': '123456',
        'password': 'Password!1234',
        'password_confirmation': 'Password!1234',
    }
    use_case_override_with_error(reset_password_factory, Exception())
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        '/api/v1/users/password/reset',
        headers=headers,
        json=body,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()
    assert response_data['error'] == 'internal error server'


async def test_should_handle_domain_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    body = {
        'email': 'email@email.com',
        'code': '123456',
        'password': 'Password!1234',
        'password_confirmation': 'Password!1234',
    }
    use_case_override_with_error(reset_password_factory, InactiveUserError())
    expected_status_code = 403

    # act
    actual_response = await async_client.post(
        '/api/v1/users/password/reset',
        headers=headers,
        json=body,
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
    body = {
        'email': 'email@email.com',
        'code': '123456',
        'password': 'Password!1234',
        'password_confirmation': 'Password!1234',
    }
    use_case_override_with_error(
        reset_password_factory, CorruptedPersistenceStateError()
    )
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        '/api/v1/users/password/reset',
        headers=headers,
        json=body,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()
    assert response_data['error'] == 'internal error server'


async def test_should_handle_application_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    body = {
        'email': 'email@email.com',
        'code': '123456',
        'password': 'Password!1234',
        'password_confirmation': 'Password!1234',
    }
    use_case_override_with_error(
        reset_password_factory, EmailAlreadyUsedError()
    )
    expected_status_code = 409

    # act
    actual_response = await async_client.post(
        '/api/v1/users/password/reset',
        headers=headers,
        json=body,
    )

    # asserts
    assert actual_response.status_code == expected_status_code
    response_data = actual_response.json()['error']
    assert response_data['code'] == 'EMAIL_ALREADY_USE'
    assert response_data['message'] == (
        'An account with this email already exists'
    )
