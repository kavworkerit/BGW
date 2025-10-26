from celery import Task
from app.celery_app import celery_app
from app.services.notification_service import NotificationService
from app.core.database import get_db


@celery_app.task(bind=True)
def send_notification(self, notification_id: str):
    """Отправить уведомление"""
    try:
        db = next(get_db())
        notification_service = NotificationService(db)
        success = notification_service.send_notification(notification_id)
        return {"status": "success", "notification_id": notification_id}
    except Exception as exc:
        self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task
def process_pending_notifications():
    """Обработать ожидающие уведомления"""
    try:
        db = next(get_db())
        notification_service = NotificationService(db)
        processed = notification_service.process_pending_notifications()
        return {"processed": processed}
    except Exception as exc:
        return {"error": str(exc)}