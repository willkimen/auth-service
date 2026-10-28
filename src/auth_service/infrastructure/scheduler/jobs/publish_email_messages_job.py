import logging

from apscheduler.schedulers.base import BaseScheduler

from auth_service.application.ports.input import PublishEmailMessagePort

logger = logging.getLogger(__name__)


async def publish_email_messages_job(use_case: PublishEmailMessagePort) -> None:
    """
    Runs the scheduled job for publishing pending email messages.

    Executes the publish email message use case and logs unexpected
    exceptions to prevent them from propagating beyond the scheduled job.

    Args:
        use_case: Input port for publishing pending email messages.
    """
    try:
        await use_case.execute()
    except Exception:
        logger.exception('Unexpected error while publishing pending email messages.')


def register_publish_email_messages_job(
    scheduler: BaseScheduler,
    use_case: PublishEmailMessagePort,
) -> None:
    scheduler.add_job(
        publish_email_messages_job,
        trigger='interval',
        seconds=10,
        kwargs={'use_case': use_case},
    )
