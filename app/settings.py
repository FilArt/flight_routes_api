from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(secrets_dir="/run/secrets")

    DB_HOST: str = "db"
    DB_NAME: str = "postgres"
    DB_USER: str = "flightsuser"
    DB_PASSWORD: str = "flightsuser"

    @property
    def db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"
