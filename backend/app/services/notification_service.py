"""Сервис уведомлений."""
import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID
import httpx
import logging
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.notification import Notification
from app.models.alert_rule import AlertRule
from app.models.listing_event import ListingEvent

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений."""

    def __init__(self, db: Session):
        self.db = db
        self.channels = {
            'webpush': WebPushChannel(),
            'telegram': TelegramChannel()
        }

    async def send_notification(self, channel: str, event_data: Dict[str, Any]) -> bool:
        """Отправить уведомление через указанный канал."""
        if channel not in self.channels:
            logger.error(f"Unknown notification channel: {channel}")
            return False

        try:
            channel_service = self.channels[channel]
            return await channel_service.send(event_data)
        except Exception as e:
            logger.error(f"Failed to send notification via {channel}: {e}")
            return False

    async def send_to_multiple_channels(self, channels: List[str], event_data: Dict[str, Any]) -> Dict[str, bool]:
        """Отправить уведомление через несколько каналов."""
        results = {}
        tasks = []

        for channel in channels:
            if channel in self.channels:
                task = asyncio.create_task(
                    self.send_notification(channel, event_data)
                )
                tasks.append((channel, task))

        for channel, task in tasks:
            try:
                results[channel] = await task
            except Exception as e:
                logger.error(f"Failed to send notification via {channel}: {e}")
                results[channel] = False

        return results

    async def process_event(self, event: ListingEvent) -> List[Notification]:
        """Обработать событие и создать уведомления по правилам."""
        notifications = []
        rules = self.db.query(AlertRule).filter(AlertRule.enabled == True).all()

        for rule in rules:
            if await self._evaluate_rule(event, rule):
                # Проверяем cooldown
                if not self._is_in_cooldown(rule):
                    notification = await self._create_notification(rule, event)
                    notifications.append(notification)

                    # Отправляем уведомление
                    await self._send_notification(notification)

        return notifications

    async def _evaluate_rule(self, event: ListingEvent, rule: AlertRule) -> bool:
        """Оценить правило для события."""
        conditions = rule.conditions

        results = []
        for condition in conditions:
            field = condition.get('field')
            op = condition.get('op')
            value = condition.get('value')

            result = self._evaluate_condition(event, field, op, value)
            results.append(result)

        # Применяем логику
        if rule.logic == 'AND':
            return all(results)
        else:  # OR
            return any(results)

    def _evaluate_condition(self, event: ListingEvent, field: str, op: str, value: Any) -> bool:
        """Оценить отдельное условие."""
        # Получаем значение из события
        event_value = getattr(event, field, None)

        if event_value is None:
            return False

        # Операторы сравнения
        if op == 'in':
            return event_value in value
        elif op == 'contains':
            return isinstance(event_value, str) and value.lower() in event_value.lower()
        elif op == 'contains_any':
            if not isinstance(event_value, str):
                return False
            return any(item.lower() in event_value.lower() for item in value)
        elif op == '>=':
            return event_value >= value
        elif op == '<=':
            return event_value <= value
        elif op == '=':
            return event_value == value
        else:
            logger.warning(f"Unknown operator: {op}")
            return False

    def _is_in_cooldown(self, rule: AlertRule) -> bool:
        """Проверить, находится ли правило в периоде cooldown."""
        # Ищем последнее уведомление по этому правилу
        last_notification = self.db.query(Notification)\
            .filter(Notification.rule_id == rule.id)\
            .order_by(Notification.created_at.desc())\
            .first()

        if not last_notification:
            return False

        cooldown_end = last_notification.created_at + timedelta(hours=rule.cooldown_hours)
        return datetime.utcnow() < cooldown_end

    async def _create_notification(self, rule: AlertRule, event: ListingEvent) -> Notification:
        """Создать уведомление."""
        notification = Notification(
            rule_id=rule.id,
            event_id=event.id,
            status='pending',
            meta={
                'rule_name': rule.name,
                'event_title': event.title,
                'event_kind': event.kind.value if event.kind else None
            }
        )

        self.db.add(notification)
        self.db.commit()
        return notification

    async def _send_notification(self, notification: Notification):
        """Отправить уведомление."""
        try:
            # Формируем данные для уведомления
            event = notification.event
            event_data = {
                'title': event.title or 'Событие',
                'store_name': event.store.name if event.store else 'Магазин',
                'price': float(event.price) if event.price else None,
                'discount_pct': float(event.discount_pct) if event.discount_pct else None,
                'in_stock': event.in_stock,
                'url': event.url,
                'kind': event.kind.value if event.kind else 'announce'
            }

            # Отправляем через все каналы правила
            results = await self.send_to_multiple_channels(
                notification.rule.channels,
                event_data
            )

            # Обновляем статус уведомления
            if any(results.values()):
                notification.status = 'sent'
                notification.sent_at = datetime.utcnow()
            else:
                notification.status = 'error'
                notification.meta['error'] = 'All channels failed'

            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to send notification {notification.id}: {e}")
            notification.status = 'error'
            notification.meta['error'] = str(e)
            self.db.commit()

    async def get_all_notifications(self) -> List[Notification]:
        """Получить все уведомления."""
        return self.db.query(Notification).order_by(Notification.created_at.desc()).all()

    async def create_rule(self, rule_data: dict) -> AlertRule:
        """Создать правило уведомлений."""
        rule = AlertRule(**rule_data)
        self.db.add(rule)
        self.db.commit()
        return rule

    async def update_rule(self, rule_id: UUID, update_data: dict) -> Optional[AlertRule]:
        """Обновить правило уведомлений."""
        rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return None

        for key, value in update_data.items():
            setattr(rule, key, value)

        self.db.commit()
        return rule

    async def delete_rule(self, rule_id: UUID) -> bool:
        """Удалить правило уведомлений."""
        rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return False

        self.db.delete(rule)
        self.db.commit()
        return True

    async def test_webpush(self) -> bool:
        """Отправить тестовое Web Push уведомление."""
        test_data = {
            'title': '🧪 Тестовое уведомление',
            'store_name': 'BGW System',
            'price': 0,
            'discount_pct': 0,
            'in_stock': True,
            'url': 'http://localhost:3000',
            'kind': 'announce'
        }
        return await self.send_notification('webpush', test_data)

    async def test_telegram(self) -> bool:
        """Отправить тестовое Telegram уведомление."""
        test_data = {
            'title': '🧪 Тестовое уведомление BGW',
            'store_name': 'BGW System',
            'price': 0,
            'discount_pct': 0,
            'in_stock': True,
            'url': 'http://localhost:3000',
            'kind': 'announce'
        }
        return await self.send_notification('telegram', test_data)

    async def test_rule(self, rule_id: UUID) -> dict:
        """Протестировать правило на последних событиях."""
        rule = self.db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return {'error': 'Rule not found'}

        # Получаем последние 50 событий
        recent_events = self.db.query(ListingEvent)\
            .order_by(ListingEvent.created_at.desc())\
            .limit(50)\
            .all()

        matched_events = []
        for event in recent_events:
            if await self._evaluate_rule(event, rule):
                matched_events.append({
                    'id': str(event.id),
                    'title': event.title,
                    'store_id': event.store_id,
                    'kind': event.kind.value if event.kind else None,
                    'created_at': event.created_at.isoformat()
                })

        return {
            'rule_id': str(rule_id),
            'rule_name': rule.name,
            'matched_events': matched_events,
            'match_count': len(matched_events)
        }


class WebPushChannel:
    """Канал Web Push уведомлений."""

    def __init__(self):
        self.vapid_public_key = settings.VAPID_PUBLIC_KEY
        self.vapid_private_key = settings.VAPID_PRIVATE_KEY
        self.vapid_email = settings.VAPID_EMAIL

    async def send(self, event_data: Dict[str, Any]) -> bool:
        """Отправить Web Push уведомление."""
        # TODO: Implement WebPush sending logic
        # Это требует интеграции с сервис-воркером на фронтенде
        logger.info(f"WebPush notification: {event_data.get('title', 'No title')}")
        return True


class TelegramChannel:
    """Канал Telegram уведомлений."""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send(self, event_data: Dict[str, Any]) -> bool:
        """Отправить Telegram уведомление."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot token or chat ID not configured")
            return False

        message = self._format_message(event_data)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False
                    }
                )

                if response.status_code == 200:
                    return True
                else:
                    logger.error(f"Telegram API error: {response.text}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
            return False

    def _format_message(self, event_data: Dict[str, Any]) -> str:
        """Форматировать сообщение для Telegram."""
        title = event_data.get('title', 'Событие')
        store_name = event_data.get('store_name', 'Магазин')
        price = event_data.get('price')
        discount_pct = event_data.get('discount_pct')
        in_stock = event_data.get('in_stock')
        url = event_data.get('url')
        kind = event_data.get('kind', 'announce')

        # Эмодзи для типов событий
        kind_emojis = {
            'announce': '📢',
            'preorder': '🎯',
            'release': '🎉',
            'discount': '💰',
            'price': '💵'
        }

        emoji = kind_emojis.get(kind, '📢')

        message_parts = [
            f"{emoji} <b>{title}</b>",
            f"🏪 Магазин: {store_name}"
        ]

        if price:
            message_parts.append(f"💳 Цена: {price} ₽")

        if discount_pct:
            message_parts.append(f"🏷️ Скидка: {discount_pct}%")

        if in_stock is not None:
            status = "✅ В наличии" if in_stock else "❌ Нет в наличии"
            message_parts.append(status)

        if url:
            message_parts.append(f"🔗 {url}")

        message_parts.append("")
        message_parts.append("🔔 Настройки уведомлений — в приложении")

        return "\n".join(message_parts)


# Функция-фабрика для создания экземпляра NotificationService
def get_notification_service(db: Session) -> NotificationService:
    """Создать экземпляр NotificationService с сессией БД."""
    return NotificationService(db)