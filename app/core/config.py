from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Events API Agregator Service"

    LOG_FORMAT: str = "json"
    LOG_HANDLERS: str = "stdout"
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5

    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "agregator_service"
    DATABASE_USERNAME: str = "postgres"
    DATABASE_PASSWORD: str = "postgres"

    EVENTS_PROVIDER_BASE_URL: str = "http://events-provider.dev-2.python-labs.ru"
    EVENTS_PROVIDER_API_KEY: str = ""

    SYNC_CRON_ENABLED: bool = True
    SYNC_CRON_HOUR: int = 3
    SYNC_CRON_MINUTE: int = 0
    SYNC_CRON_TIMEZONE: str = "UTC"

    @property
    def events_provider_base_url(self) -> str:
        return self.EVENTS_PROVIDER_BASE_URL.rstrip("/") + "/"

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DATABASE_USERNAME}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.DATABASE_USERNAME}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
