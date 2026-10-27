import pytest

from auth_service.application.messages.message import Message
from auth_service.application.messages.message_enums import MessageType
from auth_service.application.messages.payload import VerificationCodePayload


@pytest.fixture
def messages_below_max_attempts() -> list[Message]:
    """Provides a pending message that has not reached the maximum publish attempts.

    The message has zero publish attempts and is expected to be eligible
    for publication by the use case.
    """
    return [
        Message(
            type=MessageType.EMAIL_VERIFICATION_CODE,
            payload=VerificationCodePayload('user@email.com', '123456'),
        ),
    ]


@pytest.fixture
def messages_at_max_attempts() -> list[Message]:
    """Provides a pending message that has reached the maximum publish attempts.

    The message has five publish attempts, matching the use case's current
    maximum. It is expected to be marked as FAILED without another
    publication attempt.
    """
    return [
        Message(
            type=MessageType.EMAIL_VERIFICATION_CODE,
            payload=VerificationCodePayload('user@email.com', '123456'),
            publish_attempts=5,
        ),
    ]
