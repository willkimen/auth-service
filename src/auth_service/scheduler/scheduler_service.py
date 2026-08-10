from apscheduler.schedulers.base import BaseScheduler

from auth_service.scheduler.cleanup_service import CleanupService


class CleanupSchedulerService:
    def __init__(self, cleanup: CleanupService, scheduler: BaseScheduler):
        self._cleanup = cleanup
        self._scheduler = scheduler

        self._scheduler.add_job(
            self._cleanup.cleanup,
            trigger='cron',
            hour=3,
        )

    def start_scheduler(self) -> None:
        """
        Starts the application scheduler.

        Activates all registered jobs, allowing them to execute according
        to their configured schedules.
        """
        self._scheduler.start()

    def shutdown_scheduler(self) -> None:
        """
        Shuts down the application scheduler.

        Stops the scheduler and prevents any further scheduled jobs from
        being executed.
        """
        self._scheduler.shutdown()
