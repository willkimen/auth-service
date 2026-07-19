from datetime import datetime

from httpx2 import AsyncClient
from sqlalchemy import Row, TextClause
from sqlalchemy.ext.asyncio import AsyncEngine

from adapters.inputs.api.dependencies.use_cases import (
    email_verification_code_factory,
)
from application.exceptions import (
    CorruptedPersistenceStateError,
    EmailAlreadyUsedError,
)
from application.messages.message_types import MessageType
from domain.entities.user import User
from domain.enums import CodeType
from domain.exceptions import InactiveUserError, UserErrorCode

headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}


async def test_return_correctly_status_code(
    async_client: AsyncClient,
    persist_unverified_user: User,
    get_settings_override: None,
    clean_database,
):
    # arrange
    expected_status_code = 204
    body = {'email': persist_unverified_user.email.value}

    # act
    response = await async_client.post(
        '/api/v1/users/email/verify/code',
        headers=headers,
        json=body,
    )

    # assert
    assert response.status_code == expected_status_code


async def test_correctly_persists_verification_code(
    async_client: AsyncClient,
    persist_unverified_user: User,
    get_settings_override: None,
    engine: AsyncEngine,
    select_verification_code_by_user_public_id: TextClause,
    clean_database,
):
    # arrange
    body = {'email': persist_unverified_user.email.value}

    # act
    await async_client.post(
        '/api/v1/users/email/verify/code',
        headers=headers,
        json=body,
    )

    # assert
    async with engine.connect() as conn:
        row: Row | None = (
            await conn.execute(
                select_verification_code_by_user_public_id,
                {'user_public_id': persist_unverified_user.public_id},
            )
        ).fetchone()

    assert row is not None
    first = 1
    assert row.id == first
    assert row.code is not None
    assert row.user_public_id == persist_unverified_user.public_id
    assert row.type == CodeType.EMAIL_VERIFICATION
    assert isinstance(row.created_at, datetime)
    assert isinstance(row.expires_at, datetime)
    assert row.expires_at > row.created_at
    assert row.used_at is None
    assert row.payload is None


async def test_correctly_persists_message(
    async_client: AsyncClient,
    persist_unverified_user: User,
    get_settings_override: None,
    engine: AsyncEngine,
    select_first_message: TextClause,
    select_verification_code_by_user_public_id: TextClause,
    clean_database,
):
    # arrange
    body = {'email': persist_unverified_user.email.value}

    # act
    await async_client.post(
        '/api/v1/users/email/verify/code',
        headers=headers,
        json=body,
    )

    # assert
    async with engine.connect() as conn:
        message_row: Row | None = (
            await conn.execute(select_first_message)
        ).fetchone()

        verification_code_row: Row | None = (
            await conn.execute(
                select_verification_code_by_user_public_id,
                {'user_public_id': persist_unverified_user.public_id},
            )
        ).fetchone()

    assert message_row is not None
    assert message_row.type == MessageType.EMAIL_VERIFICATION_CODE
    assert isinstance(message_row.created_at, datetime)
    assert isinstance(message_row.expires_at, datetime)
    assert message_row.expires_at > message_row.created_at
    assert message_row.payload['to'] == persist_unverified_user.email.value
    assert message_row.payload['code'] == verification_code_row.code


async def test_should_handle_unexpected_exception(
    async_client: AsyncClient,
    use_case_override_with_error,
):
    # arrange
    body = {'email': 'email@email.comj'}
    use_case_override_with_error(email_verification_code_factory, Exception())
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/verify/code',
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
    body = {'email': 'email@email.comj'}
    use_case_override_with_error(
        email_verification_code_factory, InactiveUserError()
    )
    expected_status_code = 403

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/verify/code',
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
    body = {'email': 'email@email.comj'}
    use_case_override_with_error(
        email_verification_code_factory, CorruptedPersistenceStateError()
    )
    expected_status_code = 500

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/verify/code',
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
    body = {'email': 'email@email.comj'}
    use_case_override_with_error(
        email_verification_code_factory, EmailAlreadyUsedError()
    )
    expected_status_code = 409

    # act
    actual_response = await async_client.post(
        '/api/v1/users/email/verify/code',
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
