from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Базовые настройки
    PROJECT_NAME: str = "Мониторинг настольных игр"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Безопасность
    SECRET_KEY: str = "your-secret-key-here"
    CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000"]

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
    OLLAMA_URL: Optional[str] = None

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # Web Push
    VAPID_PUBLIC_KEY: Optional[str] = None
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_EMAIL: Optional[str] = None

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

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()