from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.agents",
        "app.tasks.notifications",
        "app.tasks.cleanup"
    ]
)

# Настройки Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.TZ,
    enable_utc=True,
    beat_schedule={
        "cleanup-old-data": {
            "task": "app.tasks.cleanup.cleanup_old_data",
            "schedule": 24 * 60 * 60,  # ежедневно
        },
        "backup-daily": {
            "task": "app.tasks.backup.backup_daily",
            "schedule": 24 * 60 * 60,  # ежедневно
        },
    },
)