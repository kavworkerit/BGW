"""Сервис для обработки событий."""
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.game import Game
from app.models.store import Store
from app.models.listing_event import ListingEvent, EventKind
from app.models.price_history import PriceHistory
from app.models.alert_rule import AlertRule
from app.agents.base import ListingEventDraft
from app.services.notification_service import notification_service
from app.services.game_matching_service import game_matching_service
import logging

logger = logging.getLogger(__name__)


class EventService:
    """Сервис для обработки событий."""

    async def process_event(self, db: Session, draft: ListingEventDraft, source_id: str) -> Optional[ListingEvent]:
        """Обработать черновик события и создать событие."""
        try:
            # Нормализация названия игры
            matched_game = await game_matching_service.match_game(db, draft.title)

            # Определение магазина
            store_id = draft.store_id
            if store_id:
                store = db.query(Store).filter(Store.id == store_id).first()
                if not store:
                    # Создаем магазин если его нет
                    store = Store(id=store_id, name=store_id.title())
                    db.add(store)
                    db.commit()
                    db.refresh(store)

            # Вычисляем signature_hash для дедупликации
            signature_hash = self._compute_signature_hash(draft)

            # Проверяем на дубликаты
            existing = self._find_duplicate(db, signature_hash)
            if existing:
                logger.debug(f"Duplicate event found: {draft.title}")
                return None

            # Создаем событие
            event = ListingEvent(
                game_id=matched_game.id if matched_game else None,
                store_id=store_id,
                kind=EventKind(draft.kind) if draft.kind else EventKind.ANNOUNCE,
                title=draft.title,
                edition=draft.edition,
                price=draft.price,
                currency='RUB',
                discount_pct=draft.discount_pct,
                in_stock=draft.in_stock,
                url=draft.url,
                source_id=source_id,
                signature_hash=signature_hash
            )

            db.add(event)
            db.commit()
            db.refresh(event)

            # Добавляем в историю цен если есть цена
            if draft.price and matched_game and store_id:
                price_record = PriceHistory(
                    game_id=matched_game.id,
                    store_id=store_id,
                    observed_at=datetime.now(),
                    price=draft.price,
                    currency='RUB'
                )
                db.add(price_record)
                db.commit()

            logger.info(f"Created event: {event.title}")
            return event

        except Exception as e:
            logger.error(f"Error processing event {draft.title}: {e}")
            db.rollback()
            return None

    async def check_notification_rules(self, db: Session, event: ListingEvent):
        """Проверить правила уведомлений для события."""
        rules = db.query(AlertRule).filter(AlertRule.enabled == True).all()

        for rule in rules:
            try:
                if await self._evaluate_rule(db, rule, event):
                    # Отправляем уведомление
                    await self._send_notification(db, rule, event)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.id}: {e}")

    def _compute_signature_hash(self, draft: ListingEventDraft) -> str:
        """Вычислить хэш подписи для дедупликации."""
        # Округляем цену до целых
        price_str = "null" if draft.price is None else str(int(round(draft.price)))

        # Берем время с точностью до 24 часов
        time_bucket = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # Нормализуем текст
        title_normalized = draft.title.lower().strip()

        components = [
            title_normalized,
            draft.store_id or "",
            draft.edition or "",
            price_str,
            time_bucket.isoformat()
        ]

        base = "|".join(components)
        return hashlib.sha256(base.encode()).hexdigest()

    def _find_duplicate(self, db: Session, signature_hash: str, hours: int = 24) -> Optional[ListingEvent]:
        """Найти дубликат события по хэшу."""
        since = datetime.now() - timedelta(hours=hours)
        return db.query(ListingEvent).filter(
            and_(
                ListingEvent.signature_hash == signature_hash,
                ListingEvent.created_at >= since
            )
        ).first()

    async def _evaluate_rule(self, db: Session, rule: AlertRule, event: ListingEvent) -> bool:
        """Оценить правило для события."""
        conditions = rule.conditions
        results = []

        for condition in conditions:
            field = condition['field']
            operator = condition['op']
            value = condition['value']

            # Получаем значение поля из события
            event_value = self._get_event_field(db, event, field)

            # Оцениваем условие
            result = self._evaluate_condition(event_value, operator, value)
            results.append(result)

        # Применяем логику
        if rule.logic == 'AND':
            return all(results)
        else:  # OR
            return any(results)

    def _get_event_field(self, db: Session, event: ListingEvent, field: str):
        """Получить значение поля из события."""
        if field == 'game':
            if event.game_id:
                game = db.query(Game).filter(Game.id == event.game_id).first()
                return game.title if game else None
            return None
        elif field == 'title':
            return event.title
        elif field == 'kind':
            return event.kind.value if event.kind else None
        elif field == 'price':
            return float(event.price) if event.price else None
        elif field == 'discount_pct':
            return float(event.discount_pct) if event.discount_pct else None
        elif field == 'store_id':
            return event.store_id
        elif field == 'in_stock':
            return event.in_stock
        else:
            return None

    def _evaluate_condition(self, event_value, operator: str, value) -> bool:
        """Оценить условие."""
        if event_value is None:
            return False

        if operator == 'in':
            return event_value in value
        elif operator == 'contains':
            return isinstance(event_value, str) and value in event_value
        elif operator == 'contains_any':
            return isinstance(event_value, str) and any(x in event_value for x in value)
        elif operator == '>=':
            return event_value >= value
        elif operator == '<=':
            return event_value <= value
        elif operator == '=':
            return event_value == value
        else:
            return False

    async def _send_notification(self, db: Session, rule: AlertRule, event: ListingEvent):
        """Отправить уведомление."""
        # Проверяем cooldown
        if self._is_in_cooldown(db, rule, event):
            return

        # Формируем данные уведомления
        notification_data = {
            'title': event.title,
            'game_name': self._get_event_field(db, event, 'game'),
            'store_name': event.store_id,
            'kind': event.kind.value if event.kind else 'announce',
            'price': float(event.price) if event.price else None,
            'discount_pct': float(event.discount_pct) if event.discount_pct else None,
            'in_stock': event.in_stock,
            'url': event.url
        }

        # Отправляем через все каналы правила
        results = await notification_service.send_to_multiple_channels(
            rule.channels,
            notification_data
        )

        # Сохраняем запись об уведомлении
        from app.models.notification import Notification
        from app.models.notification import NotificationStatus

        for channel, success in results.items():
            notification = Notification(
                rule_id=rule.id,
                event_id=event.id,
                status='sent' if success else 'error',
                sent_at=datetime.now() if success else None,
                meta={'channel': channel}
            )
            db.add(notification)

        db.commit()

    def _is_in_cooldown(self, db: Session, rule: AlertRule, event: ListingEvent) -> bool:
        """Проверить находится ли правило в периоде перезарядки."""
        from app.models.notification import Notification

        since = datetime.now() - timedelta(hours=rule.cooldown_hours)

        recent_notification = db.query(Notification).filter(
            and_(
                Notification.rule_id == rule.id,
                Notification.status == 'sent',
                Notification.sent_at >= since
            )
        ).first()

        return recent_notification is not None


event_service = EventService()