import uuid
from dataclasses import dataclass
from datetime import datetime

from domain.entities.verification_code import VerificationCode
from domain.enums import CodeType
from domain.value_objects.code import Code


@dataclass(frozen=True)
class VerificationCodePersistenceDTO:
    """Represents a persistence DTO for VerificationCode entities.

    Used to transfer verification code data between core and
    persistence layers.
    """

    code: str
    user_public_id: uuid.UUID
    type: str
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None = None
    sent_at: datetime | None = None
    payload: dict | None = None

    @classmethod
    def from_entity(
        cls, code: VerificationCode
    ) -> 'VerificationCodePersistenceDTO':
        """Creates a persistence DTO from a VerificationCode entity.

        Args:
            code (VerificationCode): Source entity.

        Returns:
            VerificationCodePersistenceDTO: Created DTO.
        """
        return cls(
            code=code.code.value,
            user_public_id=code.user_public_id,
            type=code.type.value,
            created_at=code.created_at,
            expires_at=code.expires_at,
            used_at=code.used_at,
            sent_at=code._sent_at,
            payload=code.payload,
        )

    def to_entity(self) -> VerificationCode:
        """Converts persistence data into a VerificationCode entity.

        Returns:
            VerificationCode: Reconstructed entity.

        Raises:
            MissingNewEmailError:
                - If type is `CHANGE_EMAIL` and payload does not
              contain `new_email`.
            ValueError:
                - If `user_public_id` is None.
                - If `code_type` is None.
                - If `created_at` is None.
                - If `expires_at` is None.
                - If `created_at` has no timezone information.
                - If `expires_at` has no timezone information.
                - If `expires_at` is earlier than `created_at`.
                - If `used_at` has no timezone information.
                - If `used_at` is earlier than `created_at`.
                - If `sent_at` has no timezone information.
                - If `sent_at` is earlier than `created_at`.
            TypeError:
                - If `user_public_id` is not UUID type.
                - If `code_type` is not CodeType type.
        """
        return VerificationCode(
            code=Code(self.code),
            user_public_id=self.user_public_id,
            type=CodeType(self.type),
            created_at=self.created_at,
            expires_at=self.expires_at,
            used_at=self.used_at,
            sent_at=self.sent_at,
            payload=self.payload,
        )
