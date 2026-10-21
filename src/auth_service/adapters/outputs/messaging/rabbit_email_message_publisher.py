"""RabbitMQ email message publisher adapter.

The publisher must be initialized by calling and awaiting `initialize()`
before any messages can be published.
"""

import json

import aio_pika
from aio_pika.abc import AbstractRobustChannel, AbstractRobustExchange

from auth_service.application.messages.message import Message


class RabbitMQEmailMessagePublisherAdapter:
    """Publishes email messages to RabbitMQ."""

    EXCHANGE_NAME = 'notifications'
    ROUTING_KEY = 'email.send'

    def __init__(self, channel: AbstractRobustChannel) -> None:
        self._channel = channel
        self._exchange: AbstractRobustExchange | None = None

    async def initialize(self) -> None:
        """
        Declares the exchange used to publish email messages.

        This method must be called and awaited before publishing any messages.
        """
        self._exchange = await self._channel.declare_exchange(
            self.EXCHANGE_NAME,
            type=aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

    async def publish(self, message: Message) -> None:
        """Publishes a message to the email service."""
        if self._exchange is None:
            raise RuntimeError(
                'Publisher has not been initialized. '
                'Call initialize() before publishing.'
            )

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
        )
