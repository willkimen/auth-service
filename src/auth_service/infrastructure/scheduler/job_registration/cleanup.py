from apscheduler.schedulers.base import BaseScheduler

from auth_service.infrastructure.scheduler.cleanup_service import CleanupService


def register_cleanup_job(
    scheduler: BaseScheduler,
    cleanup_service: CleanupService,
) -> None:
    scheduler.add_job(
        cleanup_service.cleanup,
        trigger='cron',
        hour=3,
    )
