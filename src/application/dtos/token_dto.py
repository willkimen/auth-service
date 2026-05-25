import uuid
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PayloadTokenDTO:
    """Represents decoded token payload data.

    Attributes:
        `jti` (str):
            - Unique identifier for the token.
        `sub` (uuid.UUID):
            - Subject identifier associated with the user.
        `expires_at` (datetime):
            - Timestamp indicating when the token expires.
    """

    jti: str
    sub: uuid.UUID
    expires_at: datetime


@dataclass(frozen=True)
class AccessTokenDTO:
    """Represents an access token.

    Attributes:
        `token` (str):
            - The raw encrypted access token string.
    """

    token: str


@dataclass(frozen=True)
class RefreshTokenDTO:
    """Represents a refresh token and its metadata.

    Attributes:
        `token` (str):
            - The raw encrypted refresh token string.
        `payload` (PayloadTokenDTO):
            - The decoded metadata payload of the refresh token.
    """

    token: str
    payload: PayloadTokenDTO


@dataclass(frozen=True)
class PairTokensDTO:
    """Represents a pair tokens: access and refresh.

    Attributes:
        `access` (AccessTokenDTO):
            - The generated access token data transfer object.
        `refresh` (RefreshTokenDTO):
            - The generated refresh token data transfer object.
    """

    access: AccessTokenDTO
    refresh: RefreshTokenDTO
