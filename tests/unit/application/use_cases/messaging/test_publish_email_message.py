from dataclasses import dataclass
from unittest.mock import AsyncMock

import pytest

from auth_service.application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)
from auth_service.application.messages.message import Message
from auth_service.application.ports.output import (
    MessagePublishPort,
    MessageRepositoryPort,
    UnitOfWorkPort,
)
from auth_service.application.use_cases.messaging.publish_email_message import (
    PublishEmailMessageUseCase,
)


async def test_marks_message_as_failed_when_max_publish_attempts_is_reached(
    messages_at_max_attempts: list[Message],
):
    # arrange
    mocks: DependeciesMocked = mocks_factory(messages_at_max_attempts)
    use_case = PublishEmailMessageUseCase(
        uow=mocks.uow,
        message_publisher=mocks.message_publisher,
    )
    message = messages_at_max_attempts[0]

    # act
    await use_case.execute()

    # asserts
    mocks.uow.messages.find_pending_messages_by_type.assert_awaited()
    mocks.uow.messages.update.assert_awaited_once()
    update_arg: Message = mocks.uow.messages.update.call_args[0][0]

    # both must have status: FAILED
    assert message.status == update_arg.status

    mocks.message_publisher.publish.assert_not_awaited()


async def test_publishes_pending_message_when_max_publish_attempts_is_not_reached(
    messages_below_max_attempts: list[Message],
):
    # arrange
    mocks: DependeciesMocked = mocks_factory(messages_below_max_attempts)
    use_case = PublishEmailMessageUseCase(
        uow=mocks.uow,
        message_publisher=mocks.message_publisher,
    )
    message = messages_below_max_attempts[0]

    # act
    await use_case.execute()

    # asserts
    mocks.uow.messages.find_pending_messages_by_type.assert_awaited()
    publish_arg: Message = mocks.message_publisher.publish.call_args[0][0]

    # both must have status: PENDING
    assert message.status == publish_arg.status

    mocks.message_publisher.publish.assert_awaited()
    mocks.uow.messages.update.assert_awaited_once()


async def test_execute_propagates_infrastructure_error_when_fetching_pending_messages(
    messages_below_max_attempts: list[Message],
):
    # arrange
    mocks: DependeciesMocked = mocks_factory(messages_below_max_attempts)
    use_case = PublishEmailMessageUseCase(
        uow=mocks.uow,
        message_publisher=mocks.message_publisher,
    )

    mocks.uow.messages.find_pending_messages_by_type.side_effect = InfrastructureError(
        'Some error',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute()

    # asserts
    mocks.uow.messages.find_pending_messages_by_type.assert_awaited()
    mocks.message_publisher.publish.assert_not_awaited()
    mocks.uow.messages.update.assert_not_awaited()


async def test_execute_propagates_infrastructure_error_when_publishing_message(
    messages_below_max_attempts: list[Message],
):
    # arrange
    mocks: DependeciesMocked = mocks_factory(messages_below_max_attempts)
    use_case = PublishEmailMessageUseCase(
        uow=mocks.uow,
        message_publisher=mocks.message_publisher,
    )

    mocks.message_publisher.publish.side_effect = InfrastructureError(
        'Some error',
        InfrastructureErrorCode.MESSAGING_ERROR,
        Exception(),
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute()

    # asserts
    mocks.uow.messages.find_pending_messages_by_type.assert_awaited()
    mocks.message_publisher.publish.assert_awaited()
    mocks.uow.messages.update.assert_not_awaited()


async def test_execute_propagates_infrastructure_error_when_updating_failed_message(
    messages_at_max_attempts: list[Message],
):
    # arrange
    mocks: DependeciesMocked = mocks_factory(messages_at_max_attempts)
    use_case = PublishEmailMessageUseCase(
        uow=mocks.uow,
        message_publisher=mocks.message_publisher,
    )

    # Simulates a failure when persisting the FAILED status after the
    # message has reached the maximum number of publish attempts.
    mocks.uow.messages.update.side_effect = InfrastructureError(
        'Some error',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute()

    # asserts
    mocks.uow.messages.find_pending_messages_by_type.assert_awaited()
    mocks.uow.messages.update.assert_awaited_once()
    mocks.message_publisher.publish.assert_not_awaited()


async def test_execute_propagates_infrastructure_error_when_updating_published_message(
    messages_below_max_attempts: list[Message],
):
    # arrange
    mocks: DependeciesMocked = mocks_factory(messages_below_max_attempts)
    use_case = PublishEmailMessageUseCase(
        uow=mocks.uow,
        message_publisher=mocks.message_publisher,
    )

    # Simulates a failure when persisting the message state returned by
    # the publisher after attempting to publish a pending message.
    mocks.uow.messages.update.side_effect = InfrastructureError(
        'Some error',
        InfrastructureErrorCode.DATABASE_ERROR,
        Exception(),
    )

    # act and assert
    with pytest.raises(InfrastructureError):
        await use_case.execute()

    # asserts
    mocks.uow.messages.find_pending_messages_by_type.assert_awaited()
    mocks.uow.messages.update.assert_awaited_once()
    mocks.message_publisher.publish.assert_awaited_once()


@dataclass(frozen=True)
class DependeciesMocked:
    """
    Data structure containing the mocked dependencies for the
    change email use case.
    """

    message_publisher: AsyncMock
    uow: AsyncMock


def mocks_factory(messages: list[Message]) -> DependeciesMocked:
    uow = AsyncMock(spec=UnitOfWorkPort)
    uow.messages = AsyncMock(spec=MessageRepositoryPort)
    uow.messages.find_pending_messages_by_type.return_value = messages
    message_publisher = AsyncMock(spec=MessagePublishPort)

    return DependeciesMocked(
        uow=uow,
        message_publisher=message_publisher,
    )
