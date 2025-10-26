from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.schemas.notification import Notification, NotificationResponse
from app.services.notification_service import NotificationService
from app.core.database import get_db

router = APIRouter()


class NotificationSettings(BaseModel):
    webpush: dict
    telegram: dict
    global_settings: dict


@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    channel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db=Depends(get_db)
):
    """Получить список уведомлений с фильтрацией"""
    notification_service = NotificationService(db)
    notifications = await notification_service.get_notifications(
        limit=limit,
        offset=offset,
        channel=channel,
        status=status
    )
    return notifications


@router.get("/history")
async def get_notification_history(
    days: int = Query(7, ge=1, le=90),
    channel: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db=Depends(get_db)
):
    """Получить историю уведомлений за период"""
    notification_service = NotificationService(db)
    since_date = datetime.utcnow() - timedelta(days=days)

    notifications = await notification_service.get_notifications_since(
        since_date=since_date,
        channel=channel,
        status=status
    )

    # Статистика
    total = len(notifications)
    sent = len([n for n in notifications if n.status == 'sent'])
    failed = len([n for n in notifications if n.status == 'failed'])
    pending = len([n for n in notifications if n.status == 'pending'])

    return {
        "notifications": notifications,
        "statistics": {
            "total": total,
            "sent": sent,
            "failed": failed,
            "pending": pending,
            "success_rate": (sent / max(total, 1)) * 100
        },
        "period": {
            "days": days,
            "from_date": since_date.isoformat(),
            "to_date": datetime.utcnow().isoformat()
        }
    }


@router.get("/statistics")
async def get_notification_statistics(
    days: int = Query(30, ge=1, le=365),
    db=Depends(get_db)
):
    """Получить статистику по уведомлениям"""
    notification_service = NotificationService(db)
    since_date = datetime.utcnow() - timedelta(days=days)

    stats = await notification_service.get_statistics(since_date)
    return stats


@router.get("/settings")
async def get_notification_settings(db=Depends(get_db)):
    """Получить настройки уведомлений"""
    notification_service = NotificationService(db)
    settings = await notification_service.get_settings()
    return settings


@router.put("/settings")
async def update_notification_settings(
    settings: NotificationSettings,
    db=Depends(get_db)
):
    """Обновить настройки уведомлений"""
    notification_service = NotificationService(db)
    success = await notification_service.update_settings(settings.dict())

    if success:
        return {"message": "Notification settings updated successfully", "settings": settings}
    else:
        raise HTTPException(status_code=500, detail="Failed to update notification settings")


@router.get("/subscriptions")
async def get_webpush_subscriptions(db=Depends(get_db)):
    """Получить список Web Push подписок"""
    notification_service = NotificationService(db)
    subscriptions = await notification_service.get_webpush_subscriptions()
    return {"subscriptions": subscriptions, "total": len(subscriptions)}


@router.delete("/subscriptions/{subscription_id}")
async def delete_webpush_subscription(subscription_id: UUID, db=Depends(get_db)):
    """Удалить Web Push подписку"""
    notification_service = NotificationService(db)
    success = await notification_service.delete_webpush_subscription(subscription_id)

    if success:
        return {"message": "Web Push subscription deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Web Push subscription not found")


@router.post("/test/custom")
async def send_custom_test_notification(
    title: str,
    message: str,
    channels: List[str],
    db=Depends(get_db)
):
    """Отправить кастомное тестовое уведомление"""
    notification_service = NotificationService(db)

    results = {}
    for channel in channels:
        if channel == 'webpush':
            results['webpush'] = await notification_service.test_webpush_custom(title, message)
        elif channel == 'telegram':
            results['telegram'] = await notification_service.test_telegram_custom(title, message)
        else:
            results[channel] = {"success": False, "error": "Unknown channel"}

    return {
        "message": "Custom test notifications sent",
        "results": results
    }


@router.post("/batch/retry")
async def retry_failed_notifications(
    hours: int = Query(24, ge=1, le=168, description="Период в часах"),
    limit: int = Query(50, ge=1, le=200, description="Лимит уведомлений"),
    db=Depends(get_db)
):
    """Массовый повтор неравленных уведомлений"""
    notification_service = NotificationService(db)
    since_date = datetime.utcnow() - timedelta(hours=hours)

    results = await notification_service.retry_failed_notifications(
        since_date=since_date,
        limit=limit
    )

    return results


@router.get("/queue/status")
async def get_notification_queue_status(db=Depends(get_db)):
    """Получить статус очереди уведомлений"""
    notification_service = NotificationService(db)
    status = await notification_service.get_queue_status()
    return status


@router.post("/queue/clear")
async def clear_notification_queue(
    channel: Optional[str] = Query(None, description="Канал для очистки"),
    status: Optional[str] = Query(None, description="Статус для очистки"),
    db=Depends(get_db)
):
    """Очистить очередь уведомлений"""
    notification_service = NotificationService(db)

    cleared_count = await notification_service.clear_queue(
        channel=channel,
        status=status
    )

    return {
        "message": f"Cleared {cleared_count} notifications from queue",
        "cleared_count": cleared_count
    }


@router.post("/test/webpush")
async def test_webpush_notification(db=Depends(get_db)):
    """Отправить тестовое Web Push уведомление"""
    notification_service = NotificationService(db)
    success = await notification_service.test_webpush()
    if success:
        return {"message": "Test Web Push notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Web Push notification")


@router.post("/test/telegram")
async def test_telegram_notification(db=Depends(get_db)):
    """Отправить тестовое Telegram уведомление"""
    notification_service = NotificationService(db)
    success = await notification_service.test_telegram()
    if success:
        return {"message": "Test Telegram notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Telegram notification")


@router.post("/{notification_id}/retry")
async def retry_notification(notification_id: UUID, db=Depends(get_db)):
    """Повторить отправку уведомления"""
    notification_service = NotificationService(db)
    success = await notification_service.retry_notification(notification_id)
    if success:
        return {"message": "Notification resent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to resend notification")