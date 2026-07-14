import pytest
from starlette.requests import Request


@pytest.fixture
def fake_request():
    return Request({
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'headers': [],
    })
