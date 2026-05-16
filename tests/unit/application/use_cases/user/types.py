from dataclasses import dataclass
from unittest.mock import AsyncMock, Mock


@dataclass(frozen=True)
class RegisterUserDependencies:
    hasher: Mock
    user_repo: Mock


@dataclass(frozen=True)
class SendEmailVerificationCodeDependencies:
    user_repo: AsyncMock
    uow: AsyncMock


@dataclass(frozen=True)
class EmailVerificationDependencies:
    user_repo: AsyncMock
    code_repo: AsyncMock
    uow: AsyncMock
