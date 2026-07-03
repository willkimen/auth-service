from sqlalchemy.exc import SQLAlchemyError
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
from application.exceptions import InfrastructureError, InfrastructureErrorCode
from application.ports.output import (
    MessageRepositoryPort,
    RefreshTokenRepositoryPort,
    UserRepositoryPort,
    VerificationCodeRepositoryPort,
)


class SqlAlchemyUnitOfWork:
    """
    SQLAlchemy implementation of the Unit of Work pattern.

    This implementation manages the lifecycle of a database connection
    and transaction using an `AsyncEngine`. Upon entering the context,
    it opens a new connection, starts a transaction, and instantiates
    repository implementations that share the same persistence context.

    When the context exits, the transaction is committed if no exception
    occurred; otherwise, it is rolled back. In both cases, the database
    connection is released.

    Attributes:
        `users` (`UserRepositoryPort`):
            - Repository responsible for user persistence operations.
        `codes` (`VerificationCodeRepositoryPort`):
            - Repository responsible for verification code persistence
              operations.
        `messages` (`MessageRepositoryPort`):
            - Repository responsible for message persistence
              operations.
        `tokens` (`RefreshTokenRepositoryPort`):
            - Repository responsible for refresh token persistence
              operations.
    """

    users: UserRepositoryPort
    codes: VerificationCodeRepositoryPort
    messages: MessageRepositoryPort
    tokens: RefreshTokenRepositoryPort

    def __init__(self, engine: AsyncEngine):
        """
        Initializes the Unit of Work.

        Args:
            `engine` (`AsyncEngine`):
                - `SQLAlchemy` asynchronous engine used to create
                  database connections.
        """
        self.engine = engine

    async def __aenter__(self):
        """
        Enters the transactional persistence context.

        Opens a new database connection, starts a transaction, and
        initializes repository instances that share the same connection.

        Returns:
            `SqlAlchemyUnitOfWork`:
                - The initialized Unit of Work instance.

        Raises:
            `InfrastructureError`:
                - If the persistence context cannot be initialized.
        """
        try:
            self.conn: AsyncConnection = await self.engine.connect()
            self.tx: AsyncTransaction = await self.conn.begin()

            self.users = PostgresUserRepository(self.conn)
            self.codes = PostgresVerificationCodeRepository(self.conn)
            self.tokens = PostgresRefreshTokenRepository(self.conn)
            self.messages = PostgresMessageRepository(self.conn)

            return self

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to initialize unit of work',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e

    async def __aexit__(self, exc_type, exc, tb):
        """
        Exits the transactional persistence context.

        Rolls back the transaction if an exception occurred;
        otherwise commits all pending changes. The database
        connection is always released before leaving the context.

        Raises:
            `InfrastructureError`:
                - If transaction finalization fails.
        """
        try:
            if exc_type:
                await self.tx.rollback()
            else:
                await self.tx.commit()

        except SQLAlchemyError as e:
            raise InfrastructureError(
                message='Failed to finalize unit of work',
                code=InfrastructureErrorCode.DATABASE_ERROR,
                cause=e,
            ) from e

        finally:
            try:
                await self.conn.close()
            except SQLAlchemyError as e:
                raise InfrastructureError(
                    message='Failed to close database connection',
                    code=InfrastructureErrorCode.DATABASE_ERROR,
                    cause=e,
                ) from e
