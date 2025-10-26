"""Тесты для конфигурации приложения"""
import pytest
import os
from unittest.mock import patch
from pydantic import ValidationError

from app.core.config import Settings


class TestSettings:
    """Тесты настроек приложения"""

    def test_default_settings(self):
        """Тест настроек по умолчанию"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.project_name == "BGW - Board Games Watcher"
            assert settings.version == "1.0.0"
            assert settings.debug is False
            assert settings.environment == "production"

    def test_development_settings(self):
        """Тест настроек для разработки"""
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
            settings = Settings()

            assert settings.debug is True
            assert settings.environment == "development"

    def test_database_url_validation(self):
        """Тест валидации URL базы данных"""
        with patch.dict(os.environ, {"DATABASE_URL": "invalid-url"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_database_url_valid(self):
        """Тест валидного URL базы данных"""
        valid_url = "postgresql://user:password@localhost:5432/dbname"
        with patch.dict(os.environ, {"DATABASE_URL": valid_url}):
            settings = Settings()
            assert settings.database_url == valid_url

    def test_redis_url_validation(self):
        """Тест валидации URL Redis"""
        with patch.dict(os.environ, {"REDIS_URL": "invalid-redis-url"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_redis_url_valid(self):
        """Тест валидного URL Redis"""
        valid_url = "redis://localhost:6379/0"
        with patch.dict(os.environ, {"REDIS_URL": valid_url}):
            settings = Settings()
            assert settings.redis_url == valid_url

    def test_s3_settings(self):
        """Тест настроек S3 хранилища"""
        s3_config = {
            "S3_ENDPOINT": "https://minio.example.com",
            "S3_ACCESS_KEY": "test_key",
            "S3_SECRET_KEY": "test_secret",
            "S3_BUCKET": "test-bucket"
        }

        with patch.dict(os.environ, s3_config):
            settings = Settings()

            assert settings.s3_endpoint == "https://minio.example.com"
            assert settings.s3_access_key == "test_key"
            assert settings.s3_secret_key == "test_secret"
            assert settings.s3_bucket == "test-bucket"

    def test_ollama_settings(self):
        """Тест настроек Ollama"""
        ollama_config = {
            "OLLAMA_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "llama3.1",
            "OLLAMA_TIMEOUT": "30"
        }

        with patch.dict(os.environ, ollama_config):
            settings = Settings()

            assert settings.ollama_url == "http://localhost:11434"
            assert settings.ollama_model == "llama3.1"
            assert settings.ollama_timeout == 30

    def test_ollama_disabled(self):
        """Тест отключенного Ollama"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.ollama_url is None
            assert settings.ollama_model is None
            assert settings.ollama_enabled is False

    def test_telegram_settings(self):
        """Тест настроек Telegram"""
        telegram_config = {
            "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
            "TELEGRAM_CHAT_ID": "123456789"
        }

        with patch.dict(os.environ, telegram_config):
            settings = Settings()

            assert settings.telegram_bot_token == "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
            assert settings.telegram_chat_id == "123456789"
            assert settings.telegram_enabled is True

    def test_telegram_disabled(self):
        """Тест отключенного Telegram"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.telegram_bot_token is None
            assert settings.telegram_chat_id is None
            assert settings.telegram_enabled is False

    def test_vapid_settings(self):
        """Тест настроек VAPID для Web Push"""
        vapid_config = {
            "VAPID_PUBLIC_KEY": "test_public_key",
            "VAPID_PRIVATE_KEY": "test_private_key",
            "VAPID_EMAIL": "test@example.com"
        }

        with patch.dict(os.environ, vapid_config):
            settings = Settings()

            assert settings.vapid_public_key == "test_public_key"
            assert settings.vapid_private_key == "test_private_key"
            assert settings.vapid_email == "test@example.com"

    def test_cors_origins(self):
        """Тест настроек CORS"""
        cors_origins = "http://localhost:3000,https://example.com"
        with patch.dict(os.environ, {"CORS_ORIGINS": cors_origins}):
            settings = Settings()
            assert "http://localhost:3000" in settings.cors_origins
            assert "https://example.com" in settings.cors_origins

    def test_rate_limiting_settings(self):
        """Тест настроек rate limiting"""
        rate_limit_config = {
            "RATE_LIMIT_PER_MINUTE": "100",
            "RATE_LIMIT_BURST": "50"
        }

        with patch.dict(os.environ, rate_limit_config):
            settings = Settings()

            assert settings.rate_limit_per_minute == 100
            assert settings.rate_limit_burst == 50

    def test_agent_settings(self):
        """Тест настроек агентов"""
        agent_config = {
            "AGENT_MAX_PAGES_PER_DAY": "2000",
            "AGENT_DEFAULT_TIMEOUT": "30",
            "AGENT_RETRY_ATTEMPTS": "3",
            "AGENT_RETRY_DELAY": "5"
        }

        with patch.dict(os.environ, agent_config):
            settings = Settings()

            assert settings.agent_max_pages_per_day == 2000
            assert settings.agent_default_timeout == 30
            assert settings.agent_retry_attempts == 3
            assert settings.agent_retry_delay == 5

    def test_data_retention_settings(self):
        """Тест настроек хранения данных"""
        retention_config = {
            "DATA_RETENTION_DAYS": "730",
            "PRICE_HISTORY_RETENTION_DAYS": "1095"
        }

        with patch.dict(os.environ, retention_config):
            settings = Settings()

            assert settings.data_retention_days == 730  # 2 года
            assert settings.price_history_retention_days == 1095  # 3 года

    def test_monitoring_settings(self):
        """Тест настроек мониторинга"""
        monitoring_config = {
            "PROMETHEUS_ENABLED": "true",
            "METRICS_PORT": "9090",
            "GRAFANA_ENABLED": "true"
        }

        with patch.dict(os.environ, monitoring_config):
            settings = Settings()

            assert settings.prometheus_enabled is True
            assert settings.metrics_port == 9090
            assert settings.grafana_enabled is True

    def test_logging_settings(self):
        """Тест настроек логирования"""
        logging_config = {
            "LOG_LEVEL": "DEBUG",
            "LOG_FORMAT": "json",
            "LOG_FILE": "/var/log/bgw.log"
        }

        with patch.dict(os.environ, logging_config):
            settings = Settings()

            assert settings.log_level == "DEBUG"
            assert settings.log_format == "json"
            assert settings.log_file == "/var/log/bgw.log"

    def test_cache_settings(self):
        """Тест настроек кэширования"""
        cache_config = {
            "CACHE_TTL": "3600",
            "CACHE_MAX_SIZE": "1000"
        }

        with patch.dict(os.environ, cache_config):
            settings = Settings()

            assert settings.cache_ttl == 3600
            assert settings.cache_max_size == 1000

    def test_api_settings(self):
        """Тест настроек API"""
        api_config = {
            "API_PREFIX": "/api/v1",
            "API_DOCS_URL": "/docs",
            "API_REDOC_URL": "/redoc"
        }

        with patch.dict(os.environ, api_config):
            settings = Settings()

            assert settings.api_prefix == "/api/v1"
            assert settings.api_docs_url == "/docs"
            assert settings.api_redoc_url == "/redoc"

    def test_environment_specific_overrides(self):
        """Тест переопределений для разных окружений"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "test",
            "DEBUG": "true",
            "LOG_LEVEL": "DEBUG"
        }):
            settings = Settings()

            assert settings.environment == "test"
            assert settings.debug is True
            assert settings.log_level == "DEBUG"

    def test_security_settings(self):
        """Тест настроек безопасности"""
        security_config = {
            "SECRET_KEY": "test-secret-key-for-jwt",
            "JWT_ALGORITHM": "HS256",
            "JWT_EXPIRE_MINUTES": "1440"
        }

        with patch.dict(os.environ, security_config):
            settings = Settings()

            assert settings.secret_key == "test-secret-key-for-jwt"
            assert settings.jwt_algorithm == "HS256"
            assert settings.jwt_expire_minutes == 1440

    def test_webdriver_settings(self):
        """Тест настроек WebDriver"""
        webdriver_config = {
            "WEBDRIVER_URL": "http://localhost:4444",
            "WEBDRIVER_TIMEOUT": "30",
            "WEBDRIVER_HEADLESS": "true"
        }

        with patch.dict(os.environ, webdriver_config):
            settings = Settings()

            assert settings.webdriver_url == "http://localhost:4444"
            assert settings.webdriver_timeout == 30
            assert settings.webdriver_headless is True

    def test_invalid_boolean_setting(self):
        """Тест невалидного булевого значения"""
        with patch.dict(os.environ, {"DEBUG": "invalid-boolean"}):
            # Должен вызывать ошибку валидации
            with pytest.raises(ValidationError):
                Settings()

    def test_invalid_integer_setting(self):
        """Тест невалидного целочисленного значения"""
        with patch.dict(os.environ, {"RATE_LIMIT_PER_MINUTE": "not-an-integer"}):
            with pytest.raises(ValidationError):
                Settings()

    def test_missing_required_settings(self):
        """Тест отсутствующих обязательных настроек"""
        with patch.dict(os.environ, {}, clear=True):
            # DATABASE_URL должен быть обязательным
            with pytest.raises(ValidationError):
                Settings()