import logging
from unittest.mock import AsyncMock

from auth_service.application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)
from auth_service.application.ports.input import PublishEmailMessagePort
from auth_service.infrastructure.scheduler.jobs.publish_email_messages_job import (
    publish_email_messages_job,
)


async def test_publish_email_messages_job_executes_use_case():
    use_case = AsyncMock(spec=PublishEmailMessagePort)

    await publish_email_messages_job(use_case)

    use_case.execute.assert_awaited()


async def test_publish_email_messages_job_logs_unexpected_exception(caplog):
    use_case = AsyncMock(spec=PublishEmailMessagePort)

    use_case.execute.side_effect = InfrastructureError(
        'Some error',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    with caplog.at_level(logging.ERROR):
        await publish_email_messages_job(use_case)

    use_case.execute.assert_awaited_once()

    assert 'Unexpected error while publishing pending email messages.' in caplog.text
    assert 'Some error' in caplog.text
    assert any(
        record.exc_info is not None
        and isinstance(record.exc_info[1], InfrastructureError)
        for record in caplog.records
    )
