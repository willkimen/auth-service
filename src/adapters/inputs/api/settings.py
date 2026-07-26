from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables
    and the `.env` file.

    Attributes:
        `postgres_db` (`str`):
            - Name of the PostgreSQL database.

        `postgres_user` (`str`):
            - Username used to authenticate with the PostgreSQL database.

        `postgres_password` (`str`):
            - Password used to authenticate with the PostgreSQL database.

        `postgres_host` (`str`):
            - Hostname or IP address of the PostgreSQL database server.

        `postgres_port` (`int`):
            - Port used to connect to the PostgreSQL database server.

        `code_expiration_time` (`int`):
            - Expiration time, in minutes, for generated verification codes.
              Defaults to `20`.

        `jwt_secret` (`str`):
            - Secret key used for JWT token operations.

        `sqlalchemy_database_uri` (`str`):
            - Computed SQLAlchemy database connection URI constructed from
              the PostgreSQL configuration settings.
    """

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int

    code_expiration_time: int = 20
    jwt_secret: str

    model_config = SettingsConfigDict(
        env_file='.env',
        extra='ignore',
    )

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        """
        Builds the SQLAlchemy database connection URI.

        Returns:
            `str`:
                - PostgreSQL connection URI using the configured database
                  credentials and connection parameters.
        """
        return (
            f'postgresql+psycopg://'
            f'{self.postgres_user}:'
            f'{self.postgres_password}@'
            f'{self.postgres_host}:'
            f'{self.postgres_port}/'
            f'{self.postgres_db}'
        )
