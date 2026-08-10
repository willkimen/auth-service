import asyncio
from datetime import datetime, timezone

import time_machine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from auth_service.scheduler.cleanup_service import CleanupService
from auth_service.scheduler.scheduler_service import CleanupSchedulerService

count_verification_codes = text('SELECT COUNT(*) FROM verification_codes;')
count_refresh_tokens = text('SELECT COUNT(*) FROM refresh_tokens;')


BEFORE_CLEANUP_SCHEDULE_TIME = datetime(2000, 1, 1, 0, 0, tzinfo=timezone.utc)
SCHEDULED_CLEANUP_TIME = datetime(2000, 1, 2, 3, 0, tzinfo=timezone.utc)


@time_machine.travel(BEFORE_CLEANUP_SCHEDULE_TIME)
async def test_scheduler_should_trigger_cleanup_jobs_at_scheduled_time(
    engine: AsyncEngine,
    persist_all: None,
    clean_database: None,
):
    # arrange
    scheduler_service = CleanupSchedulerService(
        CleanupService(engine),
        AsyncIOScheduler(timezone=timezone.utc),
    )

    EXPECTED_ROWS_BEFORE_CLEANUP = 2
    EXPECTED_ROWS_AFTER_CLEANUP = 0

    async with engine.connect() as conn:
        count = await conn.scalar(count_verification_codes)
        assert count == EXPECTED_ROWS_BEFORE_CLEANUP

        count = await conn.scalar(count_refresh_tokens)
        assert count == EXPECTED_ROWS_BEFORE_CLEANUP

    scheduler_service.start_scheduler()

    # act and assert
    with time_machine.travel(SCHEDULED_CLEANUP_TIME):
        # Yield execution back to the asyncio event loop so APScheduler
        # can trigger and complete the scheduled job before assertions run.
        await asyncio.sleep(0.5)
        async with engine.connect() as conn:
            count = await conn.scalar(count_verification_codes)
            assert count == EXPECTED_ROWS_AFTER_CLEANUP

            count = await conn.scalar(count_refresh_tokens)
            assert count == EXPECTED_ROWS_AFTER_CLEANUP

    scheduler_service.shutdown_scheduler()
