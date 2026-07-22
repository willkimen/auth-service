import uuid
from datetime import datetime, timedelta, timezone
from functools import lru_cache

import jwt
import pytest
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from adapters.inputs.api.app import app
from adapters.inputs.api.dependencies.adapters import get_settings
from adapters.inputs.api.settings import Settings
from adapters.outputs.repositories.user_repository import (
    PostgresUserRepository,
)
from adapters.outputs.repositories.verification_code_repository import (
    PostgresVerificationCodeRepository,
)
from domain.entities.user import User
from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.value_objects.code import Code
from domain.value_objects.email import Email
from domain.value_objects.password import PasswordHash

jwt_secret = 'super_secret_jwt_key_that_has_at_least_32_characters_long'
email_vo = Email('email@email.com')
hash_password = PasswordHash('xxxxxxxxxxxxx')
now = datetime.now(timezone.utc)


@pytest.fixture
async def async_client():
    """
    Provides an `AsyncClient` instance configured to test the FastAPI
    application in memory.

    The client uses an `ASGITransport`, eliminating the need to start an HTTP
    server. Setting `raise_app_exceptions=False` causes unhandled exceptions
    to be returned as HTTP responses (for example, 500 Internal Server Error),
    allowing them to be asserted directly.

    After each test, all overrides registered in `app.dependency_overrides`
    are cleared to prevent them from affecting subsequent tests.
    """
    transport = ASGITransport(
        app=app,
        raise_app_exceptions=False,
    )
    async with AsyncClient(
        transport=transport,
        base_url='http://testserver',
    ) as client:
        try:
            yield client
        finally:
            app.dependency_overrides.clear()


@pytest.fixture
def get_settings_override():
    """
    Override the application's `get_settings` dependency during tests.

    Instead of loading configuration from environment variables or a `.env`
    file, this fixture provides a fixed `Settings` instance with test values.
    This makes tests deterministic and independent of the developer's local
    environment.

    The database connection values **must match** the PostgreSQL container
    configuration used by the test environment (e.g., Docker Compose or
    Testcontainers). If those values differ, the application will not be able
    to connect to the test database.
    """

    @lru_cache
    def mock_get_settings() -> Settings:
        return Settings(
            postgres_db='test-auth',
            postgres_user='test',
            postgres_password='test',
            postgres_host='localhost',
            postgres_port=5432,
            jwt_secret=jwt_secret,
            code_expiration_time=20,
        )

    app.dependency_overrides[get_settings] = mock_get_settings


@pytest.fixture
def use_case_override_with_error():
    """
    Returns a helper function that overrides a use case dependency during
    tests.

    The specified dependency is replaced with a fake implementation whose
    `execute()` method raises the provided exception. This allows testing
    error scenarios, without executing the real use case logic.

    Args:
        use_case_dependency: The dependency factory to override.
        exception: The exception to raise when `execute()` is called.
    """

    def closure(use_case_dependecy, exception):
        class UseCase:
            async def execute(*args, **kwargs):
                raise exception

        def use_case_factory_mock():
            return UseCase()

        app.dependency_overrides[use_case_dependecy] = use_case_factory_mock

    return closure


@pytest.fixture
async def persist_unverified_user(engine: AsyncEngine) -> User:
    user = User(
        public_id=uuid.uuid4(),
        email=email_vo,
        hash_password=hash_password,
        email_verified=False,
        is_active=True,
        created_at=now,
        updated_at=now,
        last_login_at=None,
    )

    async with engine.begin() as conn:
        repository = PostgresUserRepository(conn)
        await repository.create(user)

    return user


@pytest.fixture
async def persist_verified_user(engine: AsyncEngine) -> User:
    user = User(
        public_id=uuid.uuid4(),
        email=email_vo,
        hash_password=hash_password,
        email_verified=True,
        is_active=True,
        created_at=now,
        updated_at=now,
        last_login_at=now + timedelta(days=1),
    )

    async with engine.begin() as conn:
        repository = PostgresUserRepository(conn)
        await repository.create(user)

    return user


@pytest.fixture
async def create_access_token(persist_verified_user: User) -> str:
    payload = {
        'jti': 'fake-jti',
        'sub': str(persist_verified_user.public_id),
        'exp': datetime.now(timezone.utc) + timedelta(minutes=5),
        'typ': 'access',
    }
    return jwt.encode(
        payload=payload,
        key=jwt_secret,
        algorithm='HS256',
    )


@pytest.fixture
async def persist_unused_verification_code(
    persist_unverified_user: User, engine: AsyncEngine
) -> VerificationCode:

    now = datetime.now(timezone.utc)
    verification_code = VerificationCode(
        code=Code.generate(),
        user_public_id=persist_unverified_user.public_id,
        type=CodeType.EMAIL_VERIFICATION,
        created_at=now,
        expires_at=now + timedelta(minutes=20),
        used_at=None,
        payload=None,
    )

    async with engine.begin() as conn:
        repository = PostgresVerificationCodeRepository(conn)
        await repository.create(verification_code)

    return verification_code
