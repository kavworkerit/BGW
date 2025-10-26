from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", case_sensitive=True)

    # Базовые настройки
    PROJECT_NAME: str = "Мониторинг настольных игр"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Безопасность
    SECRET_KEY: str = "your-secret-key-here"
    _cors_origins: str = "http://localhost,http://localhost:3000"

    @property
    def CORS_ORIGINS(self) -> list[str]:
        return [origin.strip() for origin in self._cors_origins.split(",")]

    # База данных
    DATABASE_URL: str = "postgresql+psycopg2://app:app@localhost:5432/app"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3 хранилище (MinIO)
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET: str = "raw"
    S3_SECURE: bool = False

    # Ollama (опционально)
    OLLAMA_URL: Optional[str] = "http://host.docker.internal:11434"

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # Web Push
    VAPID_PUBLIC_KEY: Optional[str] = None
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_ADMIN_EMAIL: Optional[str] = "admin@localhost"

    # Ограничения
    MAX_DAILY_PAGES: int = 1000
    DEFAULT_RPS: float = 0.3
    DEFAULT_BURST: int = 1

    # Настройки Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Логирование
    LOG_LEVEL: str = "INFO"

    # Часовой пояс
    TZ: str = "Europe/Moscow"


settings = Settings()