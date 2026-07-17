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
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_engine(settings: SettingsDep) -> AsyncEngine:
    return create_async_engine(settings.sqlalchemy_database_uri)


def get_jwt_secret(settings: SettingsDep) -> str:
    return settings.jwt_secret


def hasher_factory() -> HasherPort:
    return BcryptHasherAdapter()


def token_manager_factory(
    key: Annotated[str, Depends(get_jwt_secret)],
) -> TokenManagerPort:
    return PyJWTManagerAdapter(key)


def unit_of_work_factory(
    engine: Annotated[AsyncEngine, Depends(get_engine)],
) -> UnitOfWorkPort:
    return SqlAlchemyUnitOfWork(engine)


HasherDep = Annotated[HasherPort, Depends(hasher_factory)]
TokenManagerDep = Annotated[TokenManagerPort, Depends(token_manager_factory)]
UnitOfWorkDep = Annotated[UnitOfWorkPort, Depends(unit_of_work_factory)]
