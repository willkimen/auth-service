from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PayloadTokenDTO:
    """Represents decoded token payload data."""

    jti: str
    sub: str
    expires_at: datetime


@dataclass(frozen=True)
class AccessTokenDTO:
    """Represents an access token."""

    token: str


@dataclass(frozen=True)
class RefreshTokenDTO:
    """Represents a refresh token and its metadata."""

    token: str
    payload: PayloadTokenDTO


@dataclass(frozen=True)
class PairTokensDTO:
    """Represents a pair tokens: access and refresh."""

    access: AccessTokenDTO
    refresh: RefreshTokenDTO
