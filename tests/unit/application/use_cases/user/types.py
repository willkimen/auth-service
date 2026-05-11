from dataclasses import dataclass
from unittest.mock import Mock


@dataclass(frozen=True)
class RegisterUserDependencies:
    hasher: Mock
    user_repo: Mock
