from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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
        return (
            f'postgresql+psycopg://'
            f'{self.postgres_user}:'
            f'{self.postgres_password}@'
            f'{self.postgres_host}:'
            f'{self.postgres_port}/'
            f'{self.postgres_db}'
        )
