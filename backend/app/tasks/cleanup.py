from celery import Task
from datetime import datetime, timedelta
from app.celery_app import celery_app
from app.core.database import get_db
from sqlalchemy import text


@celery_app.task(bind=True)
def cleanup_old_data(self):
    """Очистка старых данных (старше 2 лет)"""
    try:
        db = next(get_db())
        cutoff_date = datetime.utcnow() - timedelta(days=730)  # 2 года

        # Удаление старых событий
        delete_events_query = text("""
            DELETE FROM listing_event
            WHERE created_at < :cutoff_date
        """)

        # Удаление старых уведомлений
        delete_notifications_query = text("""
            DELETE FROM notification
            WHERE sent_at < :cutoff_date
        """)

        # Удаление старых raw items из MinIO (если реализовано)
        # Это потребует отдельной логики для очистки S3

        result_events = db.execute(delete_events_query, {"cutoff_date": cutoff_date})
        result_notifications = db.execute(delete_notifications_query, {"cutoff_date": cutoff_date})

        db.commit()

        return {
            "status": "success",
            "deleted_events": result_events.rowcount,
            "deleted_notifications": result_notifications.rowcount,
            "cutoff_date": cutoff_date.isoformat()
        }

    except Exception as exc:
        db.rollback()
        self.retry(exc=exc, countdown=3600, max_retries=3)