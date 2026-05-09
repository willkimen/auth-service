from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PayloadTokenDTO:
    """Represents decoded JWT payload data."""

    jti: str
    sub: str
    expires_at: datetime


@dataclass(frozen=True)
class AccessTokenDTO:
    """Represents an access token returned by the authentication layer."""

    token: str


@dataclass(frozen=True)
class RefreshTokenDTO:
    """Represents a refresh token and its metadata."""

    token: str
    payload: PayloadTokenDTO


