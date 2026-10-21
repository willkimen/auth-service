from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from auth_service.adapters.inputs.api.app import app
from auth_service.config.settings import load_settings
from auth_service.infrastructure.database.engine import create_engine
from auth_service.scheduler.cleanup_service import CleanupService
from auth_service.scheduler.job_registration.cleanup import register_cleanup_job


@asynccontextmanager
async def lifespan(app):
    """
    Manages the application lifecycle.

    Starts the scheduler during application startup and ensures it is
    properly shut down when the application stops.
    """
    config = load_settings()
    scheduler = AsyncIOScheduler()
    cleanup = CleanupService(create_engine(config.sqlalchemy_database_uri))

    register_cleanup_job(scheduler, cleanup)

    scheduler.start()

    yield

    scheduler.shutdown()


# Registers the application's lifespan context, allowing the scheduler
# to start during startup and shut down gracefully when the application stops.
app.router.lifespan_context = lifespan
