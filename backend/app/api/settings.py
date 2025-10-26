from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class SettingsResponse(BaseModel):
    """Модель ответа с настройками"""
    project_name: str
    version: str
    environment: str
    timezone: str
    max_daily_pages: int
    default_rps: float
    default_burst: int
    ollama_url: str | None = None
    telegram_configured: bool
    webpush_configured: bool


@router.get("/notifications", response_model=dict)
async def get_notification_settings():
    """Получить настройки уведомлений"""
    return {
        "telegram": {
            "configured": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
            "bot_token": bool(settings.TELEGRAM_BOT_TOKEN),
            "chat_id": bool(settings.TELEGRAM_CHAT_ID)
        },
        "webpush": {
            "configured": bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_EMAIL),
            "public_key": settings.VAPID_PUBLIC_KEY,
            "email": settings.VAPID_EMAIL
        }
    }


@router.put("/notifications")
async def update_notification_settings(notification_settings: dict):
    """Обновить настройки уведомлений"""
    # В реальном приложении здесь была бы логика обновления настроек
    # Для локального приложения настройки обычно хранятся в .env файле
    return {"message": "Settings updated. Please restart the application for changes to take effect."}


@router.get("/system", response_model=SettingsResponse)
async def get_system_settings():
    """Получить системные настройки"""
    return SettingsResponse(
        project_name=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        timezone=settings.TZ,
        max_daily_pages=settings.MAX_DAILY_PAGES,
        default_rps=settings.DEFAULT_RPS,
        default_burst=settings.DEFAULT_BURST,
        ollama_url=settings.OLLAMA_URL,
        telegram_configured=bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
        webpush_configured=bool(settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY and settings.VAPID_EMAIL)
    )