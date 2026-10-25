"""RabbitMQ email message publisher adapter.

Initialization:
    The publisher must be initialized by calling and awaiting `initialize()`
    before any messages can be published.

Queue declaration:
    This adapter declares the exchange but does not declare a queue because
    the messaging pattern used is Publish/Subscribe. The publisher publishes
    messages to the exchange, while the consumer is responsible for declaring
    its queue and binding it to the exchange to receive the messages.
"""

import json
from datetime import UTC, datetime

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustExchange

from auth_service.application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
)
from auth_service.application.messages.message import Message
from auth_service.application.messages.message_enums import (
    MessageFailureCode,
    MessageStatus,
)


class RabbitMQEmailMessagePublisherAdapter:
    """Publishes email messages to RabbitMQ."""

    EXCHANGE_NAME = 'notifications'
    ROUTING_KEY = 'email.send'

    def __init__(self, channel: AbstractRobustChannel) -> None:
        self._channel = channel
        self._exchange: AbstractRobustExchange | None = None

    async def initialize(self) -> None:
        """Declares the exchange used to publish email messages."""
        self._exchange = await self._channel.declare_exchange(
            self.EXCHANGE_NAME,
            type=aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

    async def publish(self, message: Message) -> Message:
        """
        Attempts to publish a message to RabbitMQ and updates its state.

        Args:
            message: Message to publish.

        Returns:
            The updated message, with its publication status, attempt count,
            and failure details when applicable.

        Raises:
            InfrastructureError:
                Raised when the publisher has not been initialized.
        """

        if self._exchange is None:
            raise InfrastructureError(
                message=(
                    'Publisher has not been initialized. '
                    'Call initialize() before publishing.'
                ),
                code=InfrastructureErrorCode.MESSAGING_ERROR,
            )

        message.publish_attempts += 1

        try:
            body = json.dumps({
                'id': str(message.id),
                'type': message.type.value,
                'payload': message.payload.to_dict(),
            }).encode('utf-8')

            await self._exchange.publish(
                aio_pika.Message(
                    body=body,
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                    content_type='application/json',
                ),
                routing_key=self.ROUTING_KEY,
                timeout=10.0,
            )

        except (TypeError, ValueError) as exc:
            self._record_failure(
                message,
                MessageFailureCode.SERIALIZATION_ERROR,
                str(exc),
            )
            message.status = MessageStatus.FAILED

        except aio_pika.exceptions.PublishError as exc:
            self._record_failure(
                message,
                MessageFailureCode.MESSAGE_UNROUTABLE,
                str(exc),
            )
            message.status = MessageStatus.FAILED

        except aio_pika.exceptions.DeliveryError as exc:
            self._record_failure(
                message,
                MessageFailureCode.PUBLISH_REJECTED,
                str(exc),
            )

        except TimeoutError as exc:
            self._record_failure(
                message,
                MessageFailureCode.PUBLISH_TIMEOUT,
                str(exc),
            )

        except (aio_pika.exceptions.AMQPException, OSError) as exc:
            self._record_failure(
                message,
                MessageFailureCode.BROKER_UNAVAILABLE,
                str(exc),
            )

        else:
            message.status = MessageStatus.PUBLISHED
            message.published_at = datetime.now(UTC)
            message.failure_code = None
            message.failure_reason = None

        return message

    @staticmethod
    def _record_failure(
        message: Message,
        failure_code: MessageFailureCode,
        failure_reason: str,
    ) -> None:
        """Records a failed attempt while keeping the message pending."""
        message.failure_code = failure_code
        message.failure_reason = failure_reason
