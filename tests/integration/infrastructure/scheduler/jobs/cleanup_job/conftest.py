import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

insert_expired_verification_code = text(
    """
    INSERT INTO verification_codes (
        code,
        user_public_id,
        type,
        created_at,
        expires_at,
        used_at
    )
    VALUES
    (
        '222222',
        'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
        'email_verification',
        '2000-01-01 10:00:00+00',
        '2000-01-01 10:15:00+00',  -- Expired at 10:15 UTC
        NULL
    );
    """
)

insert_used_verification_code = text(
    """
    INSERT INTO verification_codes (
        code,
        user_public_id,
        type,
        created_at,
        expires_at,
        used_at
    )
    VALUES
    (
        '123456',
        'b1f0cd00-0d1c-5fa9-cc7e-7cc0ce491b22',
        'email_verification',
        '2000-01-01 10:00:00+00',
        '2000-01-05 10:15:00+00',
        '2000-01-05 10:05:00+00' -- Used
    );
    """
)

insert_revoked_refresh_token = text(
    """
    INSERT INTO refresh_tokens (
        jti,
        sub,
        exp,
        revoked_at,
        created_at
    )
    VALUES
    (
        'rev-token-jti-222222',
        'b1f0cd00-0d1c-5fa9-cc7e-7cc0ce491b22',
        '2000-01-05 10:15:00+00',
        '2000-01-01 10:10:00+00',  -- Revoked at 10:10
        '2000-01-01 10:00:00+00'
    );
    """
)

insert_expired_refresh_token = text(
    """
    INSERT INTO refresh_tokens (
        jti,
        sub,
        exp,
        revoked_at,
        created_at
    )
    VALUES
    (
        'exp-token-jti-111111',
        'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
        '2000-01-01 10:15:00+00',  -- Expired at 10:15 UTC
        NULL,
        '2000-01-01 10:00:00+00'
    );
    """
)


@pytest.fixture
async def persist_expired_verification_code(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.execute(insert_expired_verification_code)


@pytest.fixture
async def persist_used_verification_code(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.execute(insert_used_verification_code)


@pytest.fixture
async def persist_expired_refresh_token(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.execute(insert_expired_refresh_token)


@pytest.fixture
async def persist_revoked_refresh_token(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.execute(insert_revoked_refresh_token)


@pytest.fixture
async def persist_all(engine: AsyncEngine):
    async with engine.begin() as conn:
        await conn.execute(insert_expired_verification_code)
        await conn.execute(insert_used_verification_code)
        await conn.execute(insert_expired_refresh_token)
        await conn.execute(insert_revoked_refresh_token)
