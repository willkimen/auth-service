import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import jwt

from application.dtos.token_dto import (
    AccessTokenDTO,
    PairTokensDTO,
    PayloadTokenDTO,
    RefreshTokenDTO,
)
from application.exceptions import (
    InfrastructureError,
    InfrastructureErrorCode,
    InvalidTokenError,
    InvalidTokenErrorCode,
)


class PyJWTManagerAdapter:
    """Defines token generation and validation operations."""

    def __init__(self, key: str):
        self._key = key
        self._access_exp = timedelta(minutes=15)
        self._refresh_exp = timedelta(days=7)
        self._algorithm = 'HS256'

    def new_pair_token(self, sub: uuid.UUID) -> PairTokensDTO:
        """Generates access and refresh token pair.

        Raises:
            InfrastructureError:
                If underlying JWT library or signing mechanism fails.
        """

        try:
            access_payload = self._create_payload(sub, 'access')
            access = self._create_token(access_payload)
            access_dto = AccessTokenDTO(
                token=access, payload=PayloadTokenDTO(**access_payload)
            )

            refresh_payload = self._create_payload(sub, 'refresh')
            refresh = self._create_token(refresh_payload)
            refresh_dto = RefreshTokenDTO(
                token=refresh, payload=PayloadTokenDTO(**refresh_payload)
            )

            return PairTokensDTO(
                access=access_dto,
                refresh=refresh_dto,
            )
        except Exception as e:
            raise InfrastructureError(
                message='',
                code=InfrastructureErrorCode.AUTH_TOKEN,
                cause=e,
            )

    def new_access(self, sub: uuid.UUID) -> str:
        """Generates a new access token.

        Raises:
            InfrastructureError:
                If token signing or encoding fails unexpectedly.
        """

        try:
            return self._create_token(self._create_payload(sub, 'access'))
        except Exception as e:
            raise InfrastructureError(
                message='', code=InfrastructureErrorCode.AUTH_TOKEN, cause=e
            )

    def validate(self, token: str) -> PayloadTokenDTO:
        """Validates and decodes a JWT token.

        Raises:
            TokenError:
                If token is invalid at application level:
                - expired
                - malformed
                - invalid signature
                - invalid claims
            InfrastructureError:
                If token decoding library fails unexpectedly.
        """

        try:
            payload: dict = jwt.decode(
                jwt=token,
                key=self._key,
                algorithms=[self._algorithm],
            )
            return PayloadTokenDTO(**payload)
        except jwt.exceptions.ExpiredSignatureError as e:
            raise InvalidTokenError(InvalidTokenErrorCode.EXPIRED) from e

        except jwt.exceptions.InvalidSignatureError as e:
            raise InvalidTokenError(
                InvalidTokenErrorCode.INVALID_SIGNATURE
            ) from e

        except (
            jwt.exceptions.DecodeError,
            jwt.exceptions.InvalidAlgorithmError,
        ) as e:
            raise InvalidTokenError(InvalidTokenErrorCode.MALFORMED) from e

        except jwt.exceptions.InvalidTokenError as e:
            raise InvalidTokenError(InvalidTokenErrorCode.INVALID) from e

        except Exception as e:
            raise InfrastructureError(
                message='Unexpected error during token decoding.',
                code=InfrastructureErrorCode.UNKNOWN,
                cause=e,
            ) from e

    def _create_exp(self, typ: Literal['access', 'refresh']) -> int:
        if typ == 'access':
            exp = datetime.now(timezone.utc) + self._access_exp
        elif typ == 'refresh':
            exp = datetime.now(timezone.utc) + self._refresh_exp

        return int(exp.timestamp())

    def _create_payload(
        self,
        sub: uuid.UUID,
        typ: Literal['access', 'refresh'],
    ) -> dict:

        jti = uuid.uuid4().hex

        return {
            'jti': jti,
            'sub': str(sub),
            'exp': self._create_exp(typ),
            'typ': typ,
        }

    def _create_token(self, payload: dict) -> str:
        return jwt.encode(
            payload=payload,
            key=self._key,
            algorithm=self._algorithm,
        )
