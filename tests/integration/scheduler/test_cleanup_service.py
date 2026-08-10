from datetime import datetime, timezone

import time_machine
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from auth_service.scheduler.cleanup_service import CleanupService

count_verification_codes = text('SELECT COUNT(*) FROM verification_codes;')
count_refresh_tokens = text('SELECT COUNT(*) FROM refresh_tokens;')

EXPECTED_ROWS_BEFORE_CLEANUP = 1
EXPECTED_ROWS_AFTER_CLEANUP = 0
AFTER_EXPIRATION_TIME = datetime(2000, 1, 2, 3, 0, tzinfo=timezone.utc)


async def test_cleanup_expired_verification_code_successfully(
    engine: AsyncEngine,
    persist_expired_verification_code: None,
    clean_database: None,
):
    # arrange
    async with engine.connect() as conn:
        count = await conn.scalar(count_verification_codes)
        assert count == EXPECTED_ROWS_BEFORE_CLEANUP

    # act
    with time_machine.travel(AFTER_EXPIRATION_TIME):
        await CleanupService(engine).cleanup_expired_verification_codes()

    # assert
    async with engine.connect() as conn:
        count = await conn.scalar(count_verification_codes)
        assert count == EXPECTED_ROWS_AFTER_CLEANUP


async def test_cleanup_used_verification_code_successfully(
    engine: AsyncEngine,
    persist_used_verification_code: None,
    clean_database: None,
):
    # arrange
    async with engine.connect() as conn:
        count = await conn.scalar(count_verification_codes)
        assert count == EXPECTED_ROWS_BEFORE_CLEANUP

    # act
    await CleanupService(engine).cleanup_used_verification_codes()

    # assert
    async with engine.connect() as conn:
        count = await conn.scalar(count_verification_codes)
        assert count == EXPECTED_ROWS_AFTER_CLEANUP


async def test_cleanup_expired_refresh_token_successfully(
    engine: AsyncEngine,
    persist_expired_refresh_token: None,
    clean_database: None,
):
    # arrange
    async with engine.connect() as conn:
        count = await conn.scalar(count_refresh_tokens)
        assert count == EXPECTED_ROWS_BEFORE_CLEANUP

    # act
    with time_machine.travel(AFTER_EXPIRATION_TIME):
        await CleanupService(engine).cleanup_expired_refresh_tokens()

    # assert
    async with engine.connect() as conn:
        count = await conn.scalar(count_refresh_tokens)
        assert count == EXPECTED_ROWS_AFTER_CLEANUP


async def test_cleanup_revoked_refresh_token_successfully(
    engine: AsyncEngine,
    persist_revoked_refresh_token: None,
    clean_database: None,
):
    # arrange
    async with engine.connect() as conn:
        count = await conn.scalar(count_refresh_tokens)
        assert count == EXPECTED_ROWS_BEFORE_CLEANUP

    # act
    await CleanupService(engine).cleanup_revoked_refresh_tokens()

    # assert
    async with engine.connect() as conn:
        count = await conn.scalar(count_refresh_tokens)
        assert count == EXPECTED_ROWS_AFTER_CLEANUP


async def test_cleanup_all_successfully(
    engine: AsyncEngine,
    persist_all: None,
    clean_database: None,
):
    EXPECTED_ROWS_BEFORE_CLEANUP = 2
    EXPECTED_ROWS_AFTER_CLEANUP = 0

    # arrange
    async with engine.connect() as conn:
        count = await conn.scalar(count_refresh_tokens)
        assert count == EXPECTED_ROWS_BEFORE_CLEANUP

        count = await conn.scalar(count_verification_codes)
        assert count == EXPECTED_ROWS_BEFORE_CLEANUP

    # act
    test_time = datetime(2000, 1, 2, 3, 0, tzinfo=timezone.utc)
    with time_machine.travel(test_time):
        await CleanupService(engine).cleanup()

    # assert
    async with engine.connect() as conn:
        count = await conn.scalar(count_refresh_tokens)
        assert count == EXPECTED_ROWS_AFTER_CLEANUP

        count = await conn.scalar(count_verification_codes)
        assert count == EXPECTED_ROWS_AFTER_CLEANUP
