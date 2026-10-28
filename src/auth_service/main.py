from contextlib import asynccontextmanager

import aio_pika
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from auth_service.adapters.inputs.api.app import app
from auth_service.adapters.outputs.messaging.rabbit_email_message_publisher import (
    RabbitMQEmailMessagePublisherAdapter,
)
from auth_service.adapters.outputs.repositories.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from auth_service.application.use_cases.messaging.publish_email_message import (
    PublishEmailMessageUseCase,
)
from auth_service.config.settings import load_settings
from auth_service.infrastructure.database.engine import create_engine
from auth_service.infrastructure.scheduler.jobs.cleanup_job import (
    CleanupJob,
    register_cleanup_job,
)
from auth_service.infrastructure.scheduler.jobs.publish_email_messages_job import (
    register_publish_email_messages_job,
)


@asynccontextmanager
async def lifespan(app):
    """
    Manages the application lifecycle.

    Initializes the database and RabbitMQ resources, configures the
    scheduled jobs, and starts the scheduler during application startup.
    Ensures that the scheduler and infrastructure resources are shut
    down when the application stops.
    """
    config = load_settings()

    # Initialize shared infrastructure resources.
    engine = create_engine(config.sqlalchemy_database_uri)
    rabbitmq_conn = await aio_pika.connect_robust(config.rabbitmq_url)

    # Enable publisher confirms and raise exceptions for returned messages.
    # These settings allow the publisher adapter to handle publication
    # failures according to the configured RabbitMQ channel behavior.
    rabbitmq_channel = await rabbitmq_conn.channel(
        publisher_confirms=True,
        on_return_raises=True,
    )

    # Initialize the publisher and declare the exchange before any
    # scheduled job attempts to publish a message.
    publisher = RabbitMQEmailMessagePublisherAdapter(rabbitmq_channel)
    await publisher.initialize()

    # Compose the use case with its required output-port implementations.
    # The Unit of Work coordinates database operations and message persistence.
    uow = SqlAlchemyUnitOfWork(engine)
    publish_email_message_use_case = PublishEmailMessageUseCase(
        uow=uow,
        message_publisher=publisher,
    )

    # Configure and start scheduled background jobs.
    scheduler = AsyncIOScheduler()
    cleanup = CleanupJob(engine)

    register_cleanup_job(scheduler, cleanup)
    register_publish_email_messages_job(
        scheduler,
        publish_email_message_use_case,
    )

    scheduler.start()

    try:
        yield
    finally:
        # Stop scheduled jobs before releasing the resources they depend on.
        scheduler.shutdown()

        # Release the RabbitMQ connection and database engine.
        await rabbitmq_conn.close()
        await engine.dispose()


# Register the lifespan context so infrastructure resources and scheduled
# jobs are initialized at application startup and released at shutdown.
app.router.lifespan_context = lifespan
