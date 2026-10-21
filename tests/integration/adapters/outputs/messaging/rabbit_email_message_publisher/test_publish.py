"""Tests that messages are correctly published to RabbitMQ.

Creates a temporary queue and binds it to the publisher's exchange,
simulating a consumer to verify that published messages are correctly
routed and received with the expected content and properties.
"""

import json

import aio_pika

from auth_service.adapters.outputs.messaging.rabbit_email_message_publisher import (
    RabbitMQEmailMessagePublisherAdapter,
)
from auth_service.application.messages.message import Message


async def test_publish_message_to_rabbitmq(
    message: Message,
    connection: aio_pika.RobustConnection,
) -> None:
    # Initialize the channel variable to ensure safe cleanup if setup fails.
    channel = None

    try:
        # Open a channel over the existing RabbitMQ connection.
        channel = await connection.channel()

        # Create the publisher adapter and declare its exchange.
        adapter = RabbitMQEmailMessagePublisherAdapter(channel)
        await adapter.initialize()

        # Create an exclusive, auto-delete queue for this test.
        # The queue is removed when its exclusive connection closes.
        queue = await channel.declare_queue(
            exclusive=True,
            auto_delete=True,
        )

        # Declare the exchange used by the publisher.
        # Declaring it again is safe when its settings match the existing exchange.
        exchange = await channel.declare_exchange(
            adapter.EXCHANGE_NAME,
            type=aio_pika.ExchangeType.DIRECT,
            durable=True,
        )

        # Bind the temporary queue to the exchange using the publisher's routing key.
        # This simulates how a consumer's queue receives messages from the exchange.
        await queue.bind(
            exchange,
            routing_key=adapter.ROUTING_KEY,
        )

        # Publish the message through the adapter being tested.
        await adapter.publish(message)

        # Retrieve the published message from the temporary queue.
        # Wait up to five seconds; return None if no message is available.
        message_received = await queue.get(timeout=5, fail=False)

        # Ensure the publisher successfully delivered a message to the queue.
        assert message_received is not None

        # Deserialize the message body from JSON into a Python dictionary.
        body = json.loads(message_received.body)

        # Verify that the published message contains the expected ID, type, and payload.
        assert body == {
            'id': str(message.id),
            'type': message.type.value,
            'payload': message.payload.to_dict(),
        }

        # Verify that the message declares JSON as its content type.
        assert message_received.content_type == 'application/json'

        # Verify that the message uses persistent delivery mode.
        assert message_received.delivery_mode == aio_pika.DeliveryMode.PERSISTENT

    finally:
        # Close the channel if it was created and is still open.
        if channel is not None and not channel.is_closed:
            await channel.close()
