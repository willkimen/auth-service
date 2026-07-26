from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from adapters.inputs.api.settings import Settings
from adapters.outputs.hashers.bcrypt_hasher import (
    BcryptHasherAdapter,
)
from adapters.outputs.repositories.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from adapters.outputs.token.pyjwt_manager import (
    PyJWTManagerAdapter,
)
from application.ports.output import (
    HasherPort,
    TokenManagerPort,
    UnitOfWorkPort,
)


@lru_cache
def get_settings() -> Settings:
    """
    Provides the application settings as a cached singleton instance.

    Returns:
        `Settings`:
            - Application configuration loaded from environment variables
              and the `.env` file.
    """
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_engine(settings: SettingsDep) -> AsyncEngine:
    """
    Creates the asynchronous SQLAlchemy database engine.

    Args:
        `settings` (`Settings`):
            - Application settings containing the SQLAlchemy database
              connection URI.

    Returns:
        `AsyncEngine`:
            - Asynchronous SQLAlchemy engine used for database operations.
    """
    return create_async_engine(settings.sqlalchemy_database_uri)


def get_jwt_secret(settings: SettingsDep) -> str:
    """
    Provides the secret key used for JWT token operations.

    Args:
        `settings` (`Settings`):
            - Application settings containing the JWT secret key.

    Returns:
        `str`:
            - Secret key used to sign and validate JWT tokens.
    """
    return settings.jwt_secret


def hasher_factory() -> HasherPort:
    """
    Creates the password hashing adapter.

    Returns:
        `HasherPort`:
            - Password hashing adapter responsible for securely hashing
              and verifying passwords.
    """
    return BcryptHasherAdapter()


def token_manager_factory(
    key: Annotated[str, Depends(get_jwt_secret)],
) -> TokenManagerPort:
    """
    Creates the token management adapter.

    Args:
        `key` (`str`):
            - Secret key used by the token manager to sign and validate
              JWT tokens.

    Returns:
        `TokenManagerPort`:
            - Token management adapter responsible for generating,
              validating, and decoding authentication tokens.
    """
    return PyJWTManagerAdapter(key)


def unit_of_work_factory(
    engine: Annotated[AsyncEngine, Depends(get_engine)],
) -> UnitOfWorkPort:
    """
    Creates the SQLAlchemy unit of work.

    Args:
        `engine` (`AsyncEngine`):
            - Asynchronous SQLAlchemy engine used to manage database
              transactions and persistence operations.

    Returns:
        `UnitOfWorkPort`:
            - Unit of work implementation responsible for coordinating
              transactional operations across repositories.
    """
    return SqlAlchemyUnitOfWork(engine)


HasherDep = Annotated[HasherPort, Depends(hasher_factory)]
TokenManagerDep = Annotated[TokenManagerPort, Depends(token_manager_factory)]
UnitOfWorkDep = Annotated[UnitOfWorkPort, Depends(unit_of_work_factory)]
