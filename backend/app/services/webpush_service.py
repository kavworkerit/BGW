"""Сервис для работы с Web Push уведомлениями."""
import json
import logging
from typing import Optional, Dict, Any, List
from py_vapid import Vapid
from pywebpush import WebPusher, WebPushException

from app.core.config import settings

logger = logging.getLogger(__name__)


class WebPushService:
    """Сервис для отправки Web Push уведомлений."""

    def __init__(self):
        self.vapid_keys = self._load_or_generate_vapid_keys()
        self.vapid_claims = {
            "sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}" if settings.VAPID_ADMIN_EMAIL else None
        }

    def _load_or_generate_vapid_keys(self) -> Dict[str, str]:
        """Загрузить или сгенерировать VAPID ключи."""
        # Для разработки можно генерировать ключи каждый раз
        # В продакшене их нужно сохранять в базе или файле
        try:
            # Проверяем, есть ли ключи в настройках
            if hasattr(settings, 'VAPID_PUBLIC_KEY') and hasattr(settings, 'VAPID_PRIVATE_KEY'):
                return {
                    'public_key': settings.VAPID_PUBLIC_KEY,
                    'private_key': settings.VAPID_PRIVATE_KEY
                }

            # Генерируем новые ключи
            vapid = Vapid()
            keys = vapid.generate_keys()

            logger.info("Generated new VAPID keys")
            return {
                'public_key': keys.public_key,
                'private_key': keys.private_key
            }
        except Exception as e:
            logger.error(f"Failed to load/generate VAPID keys: {e}")
            # Возвращаем тестовые ключи для разработки
            return {
                'public_key': 'BMnz2zBw1Yz2xU3q4LQf8RJg8v9T0w1XU3q4LQf8RJg8v9T0w1X',
                'private_key': 'M2z2zBw1Yz2xU3q4LQf8RJg8v9T0w1XU3q4LQf8RJg8v9T0w1X'
            }

    def get_vapid_public_key(self) -> str:
        """Получить публичный VAPID ключ для подписки."""
        return self.vapid_keys['public_key']

    async def send_notification(
        self,
        subscription_info: Dict[str, Any],
        payload: Dict[str, Any],
        ttl: int = 86400  # 24 часа
    ) -> Dict[str, Any]:
        """Отправить Web Push уведомление."""
        try:
            # Подготавливаем payload
            message = json.dumps(payload, ensure_ascii=False)

            # Создаем WebPusher
            webpusher = WebPusher(
                subscription_info=subscription_info,
                vapid_private_key=self.vapid_keys['private_key'],
                vapid_claims=self.vapid_claims
            )

            # Отправляем уведомление
            response = await webpusher.send(message, ttl=ttl)

            return {
                'success': True,
                'status_code': response.status_code,
                'headers': dict(response.headers)
            }

        except WebPushException as e:
            logger.error(f"WebPush error: {e}")
            # Некоторые ошибки означают, что подписка больше не действительна
            if e.response and e.response.status_code in [404, 410]:
                return {
                    'success': False,
                    'error': 'Subscription expired',
                    'status_code': e.response.status_code,
                    'should_delete_subscription': True
                }

            return {
                'success': False,
                'error': str(e),
                'status_code': e.response.status_code if e.response else 500
            }
        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {e}")
            return {
                'success': False,
                'error': str(e),
                'status_code': 500
            }

    async def send_bulk_notifications(
        self,
        subscriptions: List[Dict[str, Any]],
        payload: Dict[str, Any],
        ttl: int = 86400
    ) -> Dict[str, Any]:
        """Отправить уведомление множеству подписчиков."""
        results = {
            'total': len(subscriptions),
            'success': 0,
            'failed': 0,
            'expired_subscriptions': [],
            'errors': []
        }

        for subscription in subscriptions:
            try:
                result = await self.send_notification(subscription, payload, ttl)

                if result['success']:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'subscription': subscription.get('endpoint', 'unknown'),
                        'error': result['error']
                    })

                    # Если подписка истекла, добавляем в список для удаления
                    if result.get('should_delete_subscription'):
                        results['expired_subscriptions'].append(subscription)

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'subscription': subscription.get('endpoint', 'unknown'),
                    'error': str(e)
                })

        return results

    def validate_subscription(self, subscription_info: Dict[str, Any]) -> bool:
        """Валидировать информацию о подписке."""
        required_fields = ['endpoint', 'keys']

        if not all(field in subscription_info for field in required_fields):
            return False

        keys = subscription_info['keys']
        required_key_fields = ['p256dh', 'auth']

        if not all(field in keys for field in required_key_fields):
            return False

        return True

    def create_payload(
        self,
        title: str,
        body: str,
        icon: Optional[str] = None,
        badge: Optional[str] = None,
        image: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, str]]] = None,
        url: Optional[str] = None,
        tag: Optional[str] = None,
        require_interaction: bool = False,
        silent: bool = False
    ) -> Dict[str, Any]:
        """Создать payload для уведомления."""
        payload = {
            'title': title,
            'body': body,
            'requireInteraction': require_interaction,
            'silent': silent
        }

        if icon:
            payload['icon'] = icon
        if badge:
            payload['badge'] = badge
        if image:
            payload['image'] = image
        if data:
            payload['data'] = data
        if actions:
            payload['actions'] = actions
        if url:
            payload['url'] = url
        if tag:
            payload['tag'] = tag

        return payload


# Глобальный экземпляр сервиса
webpush_service = WebPushService()