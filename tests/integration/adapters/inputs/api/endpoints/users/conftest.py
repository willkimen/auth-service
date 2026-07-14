import pytest
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine

from adapters.inputs.api.app import app
from adapters.inputs.api.dependencies.adapters import get_engine


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
def get_engine_override(engine: AsyncEngine):
    """
    Replaces the production SQLAlchemy engine
    with a test version.
    """

    def mock_get_engine():
        return engine

    app.dependency_overrides[get_engine] = mock_get_engine


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
