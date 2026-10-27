from auth_service.application.messages.message import Message
from auth_service.application.messages.message_enums import MessageStatus, MessageType
from auth_service.application.ports.output import (
    MessagePublishPort,
    UnitOfWorkPort,
)


class PublishEmailMessageUseCase:
    """
    Publishes pending email messages through the configured message publisher.

    The use case retrieves pending messages of supported types, delegates
    their publication to the message publisher, and persists their updated
    state. Messages that have reached the maximum number of publish
    attempts are marked as failed without another publication attempt.

    Attributes:
        `_MAX_ATTEMPTS` (int):
            - Maximum number of publication attempts allowed for a message
              before it is marked as failed.
        `_MESSAGE_TYPES` (tuple[MessageType, ...]):
            - Message types handled by this use case.
        `uow` (UnitOfWorkPort):
            - Port responsible for coordinating message retrieval and
              persistence of updated message states.
        `message_publisher` (MessagePublishPort):
            - Port responsible for publishing messages to the messaging
              infrastructure.
    """

    _MAX_ATTEMPTS = 5

    _MESSAGE_TYPES = (
        MessageType.EMAIL_VERIFICATION_CODE,
        MessageType.NOTIFY_EMAIL_VERIFIED,
        MessageType.RESET_PASSWORD_CODE,
        MessageType.NOTIFY_PASSWORD_RESET,
        MessageType.CHANGE_PASSWORD_CODE,
        MessageType.NOTIFY_PASSWORD_CHANGED,
        MessageType.CHANGE_EMAIL_CODE,
        MessageType.NOTIFY_EMAIL_CHANGED,
        MessageType.ACCOUNT_DELETION_CODE,
        MessageType.NOTIFY_ACCOUNT_DELETED,
    )

    def __init__(
        self,
        uow: UnitOfWorkPort,
        message_publisher: MessagePublishPort,
    ) -> None:
        self.uow = uow
        self.message_publisher = message_publisher

    async def execute(self) -> None:
        """
        Publishes pending email messages and persists their updated state.

        Raises:
            InfrastructureError: If retrieving pending messages or persisting
                their updated state fails.
        """
        messages: list[Message] = await self.uow.messages.find_pending_messages_by_type(
            types=self._MESSAGE_TYPES,
        )

        for message in messages:
            # Justification:
            # Preserve the failure code and reason from the last publish attempt to
            # retain diagnostic information. The FAILED status indicates that the
            # message will no longer be retried, while publish_attempts records the
            # number of attempts made.
            #
            # In the future, a dedicated field may be needed to distinguish the final
            # reason for failure (e.g., maximum publish attempts reached) from the
            # underlying cause recorded by the last publish attempt. For now, avoid
            # overwriting that diagnostic information or introducing an additional
            # field without a concrete need.
            if (
                message.status == MessageStatus.PENDING
                and message.publish_attempts >= self._MAX_ATTEMPTS
            ):
                message.status = MessageStatus.FAILED
                await self.uow.messages.update(message)
            else:
                updated_message = await self.message_publisher.publish(message)
                await self.uow.messages.update(updated_message)
