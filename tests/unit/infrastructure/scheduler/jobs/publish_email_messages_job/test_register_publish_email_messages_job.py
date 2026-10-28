from unittest.mock import Mock

from apscheduler.schedulers.base import BaseScheduler

from auth_service.application.ports.input import PublishEmailMessagePort
from auth_service.infrastructure.scheduler.jobs.publish_email_messages_job import (
    publish_email_messages_job,
    register_publish_email_messages_job,
)


def test_register_publish_email_messages_job():
    scheduler = Mock(spec=BaseScheduler)
    use_case = Mock(spec=PublishEmailMessagePort)

    register_publish_email_messages_job(scheduler, use_case)

    scheduler.add_job.assert_called_once_with(
        publish_email_messages_job,
        trigger='interval',
        seconds=10,
        kwargs={'use_case': use_case},
    )
