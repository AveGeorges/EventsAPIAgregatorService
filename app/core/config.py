from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.url_utils import normalize_base_url


class Settings(BaseSettings):
    PROJECT_NAME: str = "Events API Agregator Service"

    LOG_FORMAT: str = "json"
    LOG_HANDLERS: str = "stdout"
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_FILE_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_FILE_BACKUP_COUNT: int = 5

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DATABASE_NAME: str = "agregator_service"
    POSTGRES_USERNAME: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"

    EVENTS_PROVIDER_BASE_URL: str = "http://events-provider.dev-2.python-labs.ru"
    EVENTS_PROVIDER_API_KEY: str = ""

    CAPASHINO_BASE_URL: str = "http://capashino.dev-2.python-labs.ru"
    CAPASHINO_API_KEY: str = ""

    OUTBOX_POLL_INTERVAL_SECONDS: int = 10
    OUTBOX_WORKER_ENABLED: bool = True

    GLITCHTIP_DSN: str = ""
    SENTRY_DSN: str = ""

    SYNC_CRON_ENABLED: bool = True
    SYNC_CRON_HOUR: int = 3
    SYNC_CRON_MINUTE: int = 0
    SYNC_CRON_TIMEZONE: str = "UTC"

    SEATS_CACHE_TTL_SECONDS: int = Field(default=30, ge=1)

    @property
    def events_provider_base_url(self) -> str:
        return normalize_base_url(self.EVENTS_PROVIDER_BASE_URL)

    @property
    def capashino_base_url(self) -> str:
        return normalize_base_url(self.CAPASHINO_BASE_URL)

    @property
    def glitchtip_dsn(self) -> str:
        return self.GLITCHTIP_DSN or self.SENTRY_DSN

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USERNAME}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE_NAME}"
        )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USERNAME}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DATABASE_NAME}"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
