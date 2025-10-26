"""Сервис уведомлений."""
import json
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для отправки уведомлений."""

    def __init__(self):
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


notification_service = NotificationService()