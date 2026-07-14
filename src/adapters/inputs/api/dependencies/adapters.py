from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

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

engine = create_async_engine('postgresql+psycopg://user:password@host/dbname')

JWT_KEY = 'fake-key'


def get_engine() -> AsyncEngine:
    return engine


def get_key() -> str:
    return JWT_KEY


def hasher_factory() -> HasherPort:
    return BcryptHasherAdapter()


def token_manager_factory(
    key: Annotated[str, Depends(get_key)],
) -> TokenManagerPort:
    return PyJWTManagerAdapter(key)


def unit_of_work_factory(
    engine: Annotated[AsyncEngine, Depends(get_engine)],
) -> UnitOfWorkPort:
    return SqlAlchemyUnitOfWork(engine)


HasherDep = Annotated[HasherPort, Depends(hasher_factory)]
TokenManagerDep = Annotated[TokenManagerPort, Depends(token_manager_factory)]
UnitOfWorkDep = Annotated[UnitOfWorkPort, Depends(unit_of_work_factory)]
