from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
import logging

from app.core.database import get_db
from app.models.webpush_subscription import WebPushSubscription
from app.services.webpush_service import webpush_service
from app.schemas.webpush import (
    WebPushSubscriptionCreate,
    WebPushSubscriptionResponse,
    WebPushNotificationSend,
    WebPushTestPayload
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Получить публичный VAPID ключ для подписки."""
    return {
        "public_key": webpush_service.get_vapid_public_key()
    }


@router.post("/subscribe")
async def subscribe(
    subscription_data: WebPushSubscriptionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Подписаться на Web Push уведомления."""
    try:
        # Валидация подписки
        if not webpush_service.validate_subscription(subscription_data.dict()):
            raise HTTPException(400, "Invalid subscription data")

        # Генерируем уникальный ID
        subscription_id = str(uuid.uuid4())

        # Получаем IP адрес
        ip_address = request.client.host
        if "x-forwarded-for" in request.headers:
            ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()

        # Проверяем, существует ли уже такая подписка
        existing = db.query(WebPushSubscription).filter(
            WebPushSubscription.endpoint == subscription_data.endpoint
        ).first()

        if existing:
            # Обновляем существующую подписку
            existing.p256dh_key = subscription_data.keys.p256dh
            existing.auth_key = subscription_data.keys.auth
            existing.user_agent = subscription_data.user_agent
            existing.ip_address = ip_address
            existing.is_active = True
            existing.last_used_at = None
            subscription_id = existing.id
        else:
            # Создаем новую подписку
            subscription = WebPushSubscription(
                id=subscription_id,
                user_agent=subscription_data.user_agent,
                endpoint=subscription_data.endpoint,
                p256dh_key=subscription_data.keys.p256dh,
                auth_key=subscription_data.keys.auth,
                ip_address=ip_address
            )
            db.add(subscription)

        db.commit()

        return WebPushSubscriptionResponse(
            id=subscription_id,
            status="subscribed"
        )

    except Exception as e:
        logger.error(f"Error subscribing to push notifications: {e}")
        db.rollback()
        raise HTTPException(500, "Failed to subscribe")


@router.post("/unsubscribe/{subscription_id}")
async def unsubscribe(subscription_id: str, db: Session = Depends(get_db)):
    """Отписаться от Web Push уведомлений."""
    try:
        subscription = db.query(WebPushSubscription).filter(
            WebPushSubscription.id == subscription_id
        ).first()

        if not subscription:
            raise HTTPException(404, "Subscription not found")

        # Отмечаем как неактивную вместо удаления
        subscription.is_active = False
        db.commit()

        return {"status": "unsubscribed"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing from push notifications: {e}")
        db.rollback()
        raise HTTPException(500, "Failed to unsubscribe")


@router.post("/test")
async def test_notification(
    payload: WebPushTestPayload,
    db: Session = Depends(get_db)
):
    """Отправить тестовое уведомление."""
    try:
        # Получаем активные подписки
        subscriptions = db.query(WebPushSubscription).filter(
            WebPushSubscription.is_active == True
        ).all()

        if not subscriptions:
            raise HTTPException(404, "No active subscriptions found")

        # Подготавливаем payload
        notification_payload = webpush_service.create_payload(
            title=payload.title,
            body=payload.body,
            icon=payload.icon,
            badge=payload.badge,
            data=payload.data or {},
            tag="test",
            require_interaction=payload.require_interaction
        )

        # Отправляем уведомления
        subscription_infos = [sub.subscription_info for sub in subscriptions]
        results = await webpush_service.send_bulk_notifications(
            subscription_infos,
            notification_payload
        )

        # Обрабатываем истекшие подписки
        if results['expired_subscriptions']:
            expired_endpoints = [sub['endpoint'] for sub in results['expired_subscriptions']]
            db.query(WebPushSubscription).filter(
                WebPushSubscription.endpoint.in_(expired_endpoints)
            ).update({"is_active": False}, synchronize_session=False)
            db.commit()

        return {
            "status": "sent",
            "results": results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        raise HTTPException(500, "Failed to send test notification")


@router.get("/subscriptions")
async def get_subscriptions(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Получить список подписок (для админки)."""
    try:
        query = db.query(WebPushSubscription)

        if active_only:
            query = query.filter(WebPushSubscription.is_active == True)

        subscriptions = query.order_by(WebPushSubscription.created_at.desc()).all()

        return [
            {
                "id": sub.id,
                "user_agent": sub.user_agent,
                "endpoint": sub.endpoint[:100] + "..." if len(sub.endpoint) > 100 else sub.endpoint,
                "ip_address": sub.ip_address,
                "created_at": sub.created_at,
                "last_used_at": sub.last_used_at,
                "is_active": sub.is_active
            }
            for sub in subscriptions
        ]

    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(500, "Failed to get subscriptions")


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str, db: Session = Depends(get_db)):
    """Удалить подписку."""
    try:
        subscription = db.query(WebPushSubscription).filter(
            WebPushSubscription.id == subscription_id
        ).first()

        if not subscription:
            raise HTTPException(404, "Subscription not found")

        db.delete(subscription)
        db.commit()

        return {"status": "deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        db.rollback()
        raise HTTPException(500, "Failed to delete subscription")


@router.post("/cleanup")
async def cleanup_expired_subscriptions(db: Session = Depends(get_db)):
    """Очистить истекшие подписки."""
    try:
        # Удаляем подписки, неактивные более 30 дней
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=30)

        deleted_count = db.query(WebPushSubscription).filter(
            WebPushSubscription.is_active == False,
            WebPushSubscription.created_at < cutoff_date
        ).delete()

        db.commit()

        return {
            "status": "cleaned",
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"Error cleaning up subscriptions: {e}")
        db.rollback()
        raise HTTPException(500, "Failed to cleanup subscriptions")