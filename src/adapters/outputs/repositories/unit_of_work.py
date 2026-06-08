from typing import Self

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncTransaction,
)

from adapters.outputs.repositories.message_repository import (
    PostgresMessageRepository,
)
from adapters.outputs.repositories.refresh_token_repository import (
    PostgresRefreshTokenRepository,
)
from adapters.outputs.repositories.user_repository import (
    PostgresUserRepository,
)
from adapters.outputs.repositories.verification_code_repository import (
    PostgresVerificationCodeRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    async def __aenter__(self) -> Self:
        self.conn: AsyncConnection = await self.engine.connect()
        self.tx: AsyncTransaction = await self.conn.begin()

        self.user_repo = PostgresUserRepository(self.conn)
        self.code_repo = PostgresVerificationCodeRepository(self.conn)
        self.token_repo = PostgresRefreshTokenRepository(self.conn)
        self.message_repo = PostgresMessageRepository(self.conn)

        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc_type:
            await self.tx.rollback()
        else:
            await self.tx.commit()

        await self.conn.close()
