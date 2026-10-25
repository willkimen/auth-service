import pytest

from auth_service.application.messages.message_enums import MessageType
from auth_service.application.messages.payload import (
    NotificationPayload,
    VerificationCodePayload,
    payload_from_dict,
)


@pytest.mark.parametrize(
    ('message_type', 'expected_payload_type', 'data'),
    [
        (
            MessageType.EMAIL_VERIFICATION_CODE,
            VerificationCodePayload,
            {'recipient': 'user@example.com', 'code': '123456'},
        ),
        (
            MessageType.NOTIFY_EMAIL_VERIFIED,
            NotificationPayload,
            {'recipient': 'user@example.com'},
        ),
        (
            MessageType.RESET_PASSWORD_CODE,
            VerificationCodePayload,
            {'recipient': 'user@example.com', 'code': '234567'},
        ),
        (
            MessageType.NOTIFY_PASSWORD_RESET,
            NotificationPayload,
            {'recipient': 'user@example.com'},
        ),
        (
            MessageType.CHANGE_PASSWORD_CODE,
            VerificationCodePayload,
            {'recipient': 'user@example.com', 'code': '345678'},
        ),
        (
            MessageType.NOTIFY_PASSWORD_CHANGED,
            NotificationPayload,
            {'recipient': 'user@example.com'},
        ),
        (
            MessageType.CHANGE_EMAIL_CODE,
            VerificationCodePayload,
            {'recipient': 'user@example.com', 'code': '456789'},
        ),
        (
            MessageType.NOTIFY_EMAIL_CHANGED,
            NotificationPayload,
            {'recipient': 'user@example.com'},
        ),
        (
            MessageType.ACCOUNT_DELETION_CODE,
            VerificationCodePayload,
            {'recipient': 'user@example.com', 'code': '567890'},
        ),
        (
            MessageType.NOTIFY_ACCOUNT_DELETED,
            NotificationPayload,
            {'recipient': 'user@example.com'},
        ),
    ],
)
def test_payload_from_dict_returns_correct_payload(
    message_type,
    expected_payload_type,
    data,
):
    payload = payload_from_dict(message_type, data)

    assert isinstance(payload, expected_payload_type)
    assert payload.to_dict() == data


def test_payload_from_dict_reconstructs_verification_code_payload():
    data = {'recipient': 'user@example.com', 'code': '123456'}

    payload = payload_from_dict(
        MessageType.EMAIL_VERIFICATION_CODE,
        data,
    )

    assert payload == VerificationCodePayload(
        recipient='user@example.com',
        code='123456',
    )


def test_payload_from_dict_reconstructs_notification_payload():
    data = {'recipient': 'user@example.com'}

    payload = payload_from_dict(
        MessageType.NOTIFY_EMAIL_VERIFIED,
        data,
    )

    assert payload == NotificationPayload(
        recipient='user@example.com',
    )


def test_payload_from_dict_raises_type_error_for_missing_required_field():
    with pytest.raises(TypeError):
        payload_from_dict(
            MessageType.EMAIL_VERIFICATION_CODE,
            {'recipient': 'user@example.com'},
        )
