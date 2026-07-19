from datetime import datetime
from uuid import UUID

from httpx2 import AsyncClient
from sqlalchemy import TextClause
from sqlalchemy.ext.asyncio import AsyncEngine

from adapters.inputs.api.dependencies.use_cases import register_factory
from application.exceptions import (
    CorruptedPersistenceStateError,
    EmailAlreadyUsedError,
)
from domain.exceptions import InactiveUserError, UserErrorCode

body = {'email': 'email@email.com', 'password': 'Password10!'}

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


async def test_return_correctly_response_data(
    async_client: AsyncClient,
    clean_database: None,
    get_settings_override: None,
):
    # arrange
    expected_status_code = 200

    # act
    response = await async_client.post(
        'api/v1/users/register',
        headers=headers,
        json=body,
    )

    # asserts
    response_data = response.json()

    assert response.status_code == expected_status_code
    assert 'public_id' in response_data
    assert 'created_at' in response_data
    assert response_data['email'] == body['email']
    assert response_data['email_verified'] is False
    assert response_data['last_login_at'] is None

    assert 'password' not in response_data


async def test_persists_user_correctly(
    async_client: AsyncClient,
    clean_database: None,
    engine: AsyncEngine,
    get_settings_override: None,
    select_user_by_public_id: TextClause,
):
    # act
    response = await async_client.post(
        'api/v1/users/register',
        headers=headers,
        json=body,
    )

    # asserts
    response_data = response.json()

    async with engine.connect() as conn:
        row = (
            await conn.execute(
                select_user_by_public_id,
                {'public_id': response_data['public_id']},
            )
        ).fetchone()

    assert row is not None
    assert row.last_login_at is None
    assert row.is_active is True
    assert row.email_verified is False
    assert isinstance(row.public_id, UUID)
    assert isinstance(row.created_at, datetime)
    assert row.updated_at == row.created_at

    assert str(row.public_id) == response_data['public_id']
    assert row.email == response_data['email'] == body['email']
    assert row.email_verified == response_data['email_verified']
    assert row.last_login_at == response_data['last_login_at']
    assert row.hash_password != body['password']
    db_created_string = row.created_at.isoformat().replace('+00:00', 'Z')
    assert db_created_string == response_data['created_at']


async def test_should_handle_unexpected_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    use_case_override_with_error(register_factory, Exception())
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        'api/v1/users/register',
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
    use_case_override_with_error(register_factory, InactiveUserError())
    expected_status_code = 403

    # act
    actual_response = await async_client.post(
        'api/v1/users/register',
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
    use_case_override_with_error(
        register_factory, CorruptedPersistenceStateError()
    )
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        'api/v1/users/register',
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
    use_case_override_with_error(register_factory, EmailAlreadyUsedError())
    expected_status_code = 409

    # act
    actual_response = await async_client.post(
        'api/v1/users/register',
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
