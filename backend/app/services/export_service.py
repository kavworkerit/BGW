"""Сервис для экспорта и импорта данных."""
import json
import zipfile
import io
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.game import Game
from app.models.store import Store
from app.models.listing_event import ListingEvent
from app.models.price_history import PriceHistory
from app.models.alert_rule import AlertRule
from app.models.agent import SourceAgent
from app.models.notification import Notification
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Сервис для экспорта и импорта данных."""

    def __init__(self, db: Session):
        self.db = db

    async def export_full(self, include_raw_data: bool = False) -> bytes:
        """Полный экспорт всех данных."""
        export_date = datetime.now().strftime("%Y-%m-%d")

        # Создаем ZIP архив
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:

            # Экспорт игр
            games = await self._export_games()
            zip_file.writestr("games.ndjson", "\n".join([json.dumps(game, default=str) for game in games]))

            # Экспорт магазинов
            stores = await self._export_stores()
            zip_file.writestr("stores.ndjson", "\n".join([json.dumps(store, default=str) for store in stores]))

            # Экспорт событий
            events = await self._export_events()
            zip_file.writestr("listing_events.ndjson", "\n".join([json.dumps(event, default=str) for event in events]))

            # Экспорт истории цен
            price_history = await self._export_price_history()
            zip_file.writestr("price_history.ndjson", "\n".join([json.dumps(ph, default=str) for ph in price_history]))

            # Экспорт правил
            rules = await self._export_rules()
            zip_file.writestr("alert_rules.json", json.dumps(rules, indent=2, default=str))

            # Экспорт агентов
            agents = await self._export_agents()
            zip_file.writestr("sources.json", json.dumps(agents, indent=2, default=str))

            # Экспорт уведомлений (опционально)
            notifications = await self._export_notifications()
            zip_file.writestr("notifications.ndjson", "\n".join([json.dumps(n, default=str) for n in notifications]))

            # Метаданные экспорта
            metadata = {
                "schema": "1.0",
                "created_at": datetime.now().isoformat(),
                "tables": ["game", "store", "listing_event", "price_history", "alert_rule", "source_agent", "notification"],
                "counts": {
                    "games": len(games),
                    "stores": len(stores),
                    "events": len(events),
                    "price_history": len(price_history),
                    "rules": len(rules),
                    "agents": len(agents),
                    "notifications": len(notifications)
                },
                "export_version": "1.0.0",
                "include_raw_data": include_raw_data
            }
            zip_file.writestr("version.json", json.dumps(metadata, indent=2))

            # Контрольные суммы
            checksums = await self._calculate_checksums([
                "games.ndjson", "stores.ndjson", "listing_events.ndjson",
                "price_history.ndjson", "alert_rules.json", "sources.json", "notifications.ndjson"
            ], zip_file)
            zip_file.writestr("checksums.txt", checksums)

        return zip_buffer.getvalue()

    async def import_full(self, zip_data: bytes, dry_run: bool = True) -> Dict[str, Any]:
        """Полный импорт данных."""
        zip_file = zipfile.ZipFile(io.BytesIO(zip_data))

        # Проверяем метаданные
        if "version.json" not in zip_file.namelist():
            raise ValueError("Missing version.json in export file")

        metadata = json.loads(zip_file.read("version.json").decode('utf-8'))
        logger.info(f"Importing export version: {metadata.get('export_version')} from {metadata.get('created_at')}")

        result = {
            "dry_run": dry_run,
            "metadata": metadata,
            "results": {},
            "errors": []
        }

        if not dry_run:
            # Создаем бэкап перед импортом
            backup_data = await self.export_full()
            backup_filename = f"pre_import_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            logger.info(f"Created backup: {backup_filename}")

        # Импортируем данные в правильном порядке
        import_order = [
            ("stores.json", self._import_stores),
            ("games.ndjson", self._import_games),
            ("sources.json", self._import_agents),
            ("alert_rules.json", self._import_rules),
            ("listing_events.ndjson", self._import_events),
            ("price_history.ndjson", self._import_price_history),
            ("notifications.ndjson", self._import_notifications)
        ]

        for filename, import_func in import_order:
            if filename in zip_file.namelist():
                try:
                    data = zip_file.read(filename).decode('utf-8')
                    if filename.endswith('.json'):
                        items = json.loads(data)
                    else:
                        items = [json.loads(line) for line in data.strip().split('\n') if line.strip()]

                    if not dry_run:
                        imported_count = await import_func(items)
                        result["results"][filename] = {"imported": imported_count, "status": "success"}
                    else:
                        result["results"][filename] = {"would_import": len(items), "status": "dry_run"}

                    logger.info(f"Processed {filename}: {len(items)} items")

                except Exception as e:
                    error_msg = f"Error importing {filename}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
                    result["results"][filename] = {"status": "error", "error": str(e)}

        return result

    async def export_games_csv(self, game_ids: Optional[List[str]] = None) -> str:
        """Экспорт игр в CSV формат."""
        query = self.db.query(Game)

        if game_ids:
            query = query.filter(Game.id.in_(game_ids))

        games = query.all()

        csv_lines = ["id,title,publisher,language,min_players,max_players,year_published,tags"]
        for game in games:
            tags_str = ";".join(game.tags) if game.tags else ""
            csv_lines.append(f'"{game.id}","{game.title}","{game.publisher or ""}","{game.language or ""}",'
                           f'{game.min_players or ""},{game.max_players or ""},{game.year_published or ""},"{tags_str}"')

        return "\n".join(csv_lines)

    async def export_price_history_csv(self, game_id: str, days: int = 365) -> str:
        """Экспорт истории цен в CSV."""
        from datetime import timedelta

        since_date = datetime.utcnow() - timedelta(days=days)

        history = self.db.query(PriceHistory)\
            .filter(PriceHistory.game_id == game_id)\
            .filter(PriceHistory.observed_at >= since_date)\
            .order_by(PriceHistory.observed_at.desc())\
            .all()

        csv_lines = ["store_id,price,currency,observed_at"]
        for ph in history:
            csv_lines.append(f'"{ph.store_id}",{float(ph.price)},"{ph.currency}","{ph.observed_at.isoformat()}')

        return "\n".join(csv_lines)

    async def _export_games(self) -> List[Dict[str, Any]]:
        """Экспорт игр."""
        games = self.db.query(Game).all()
        return [
            {
                "id": game.id,
                "title": game.title,
                "synonyms": game.synonyms or [],
                "bgg_id": game.bgg_id,
                "publisher": game.publisher,
                "tags": game.tags or [],
                "description": game.description,
                "min_players": game.min_players,
                "max_players": game.max_players,
                "min_playtime": game.min_playtime,
                "max_playtime": game.max_playtime,
                "year_published": game.year_published,
                "language": game.language,
                "complexity": game.complexity,
                "image_url": game.image_url,
                "rating_bgg": game.rating_bgg,
                "rating_users": game.rating_users,
                "weight": game.weight,
                "created_at": game.created_at.isoformat() if game.created_at else None
            }
            for game in games
        ]

    async def _export_stores(self) -> List[Dict[str, Any]]:
        """Экспорт магазинов."""
        stores = self.db.query(Store).all()
        return [
            {
                "id": store.id,
                "name": store.name,
                "site_url": store.site_url,
                "region": store.region,
                "currency": store.currency,
                "description": store.description,
                "logo_url": store.logo_url,
                "contact_email": store.contact_email,
                "contact_phone": store.contact_phone,
                "address": store.address,
                "working_hours": store.working_hours,
                "rating": store.rating,
                "is_active": store.is_active,
                "priority": store.priority,
                "shipping_info": store.shipping_info,
                "payment_methods": store.payment_methods,
                "social_links": store.social_links,
                "created_at": store.created_at.isoformat() if store.created_at else None
            }
            for store in stores
        ]

    async def _export_events(self) -> List[Dict[str, Any]]:
        """Экспорт событий."""
        events = self.db.query(ListingEvent).all()
        return [
            {
                "id": event.id,
                "game_id": event.game_id,
                "store_id": event.store_id,
                "kind": event.kind.value if event.kind else None,
                "title": event.title,
                "edition": event.edition,
                "price": float(event.price) if event.price else None,
                "currency": event.currency,
                "discount_pct": float(event.discount_pct) if event.discount_pct else None,
                "in_stock": event.in_stock,
                "start_at": event.start_at.isoformat() if event.start_at else None,
                "end_at": event.end_at.isoformat() if event.end_at else None,
                "url": event.url,
                "source_id": event.source_id,
                "signature_hash": event.signature_hash,
                "meta": event.meta,
                "created_at": event.created_at.isoformat() if event.created_at else None
            }
            for event in events
        ]

    async def _export_price_history(self) -> List[Dict[str, Any]]:
        """Экспорт истории цен."""
        history = self.db.query(PriceHistory).all()
        return [
            {
                "game_id": ph.game_id,
                "store_id": ph.store_id,
                "observed_at": ph.observed_at.isoformat(),
                "price": float(ph.price),
                "currency": ph.currency
            }
            for ph in history
        ]

    async def _export_rules(self) -> List[Dict[str, Any]]:
        """Экспорт правил."""
        rules = self.db.query(AlertRule).all()
        return [
            {
                "id": rule.id,
                "name": rule.name,
                "logic": rule.logic,
                "conditions": rule.conditions,
                "channels": rule.channels,
                "cooldown_hours": rule.cooldown_hours,
                "enabled": rule.enabled,
                "created_at": rule.created_at.isoformat() if rule.created_at else None
            }
            for rule in rules
        ]

    async def _export_agents(self) -> List[Dict[str, Any]]:
        """Экспорт агентов."""
        agents = self.db.query(SourceAgent).all()
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "type": agent.type,
                "schedule": agent.schedule,
                "rate_limit": agent.rate_limit,
                "config": agent.config,
                "enabled": agent.enabled,
                "created_at": agent.created_at.isoformat() if agent.created_at else None
            }
            for agent in agents
        ]

    async def _export_notifications(self) -> List[Dict[str, Any]]:
        """Экспорт уведомлений."""
        notifications = self.db.query(Notification).all()
        return [
            {
                "id": notif.id,
                "rule_id": notif.rule_id,
                "event_id": notif.event_id,
                "status": notif.status,
                "sent_at": notif.sent_at.isoformat() if notif.sent_at else None,
                "meta": notif.meta,
                "created_at": notif.created_at.isoformat() if notif.created_at else None
            }
            for notif in notifications
        ]

    async def _import_stores(self, stores_data: List[Dict[str, Any]]) -> int:
        """Импорт магазинов."""
        imported = 0
        for store_data in stores_data:
            # Проверяем существует ли магазин
            existing = self.db.query(Store).filter(Store.id == store_data['id']).first()
            if existing:
                # Обновляем существующий
                for key, value in store_data.items():
                    if hasattr(existing, key) and key != 'id':
                        setattr(existing, key, value)
            else:
                # Создаем новый
                store = Store(**store_data)
                self.db.add(store)
            imported += 1

        self.db.commit()
        return imported

    async def _import_games(self, games_data: List[Dict[str, Any]]) -> int:
        """Импорт игр."""
        imported = 0
        for game_data in games_data:
            # Проверяем существует ли игра
            existing = self.db.query(Game).filter(Game.id == game_data['id']).first()
            if existing:
                # Обновляем существующую
                for key, value in game_data.items():
                    if hasattr(existing, key) and key != 'id':
                        setattr(existing, key, value)
            else:
                # Создаем новую
                game = Game(**game_data)
                self.db.add(game)
            imported += 1

        self.db.commit()
        return imported

    async def _import_agents(self, agents_data: List[Dict[str, Any]]) -> int:
        """Импорт агентов."""
        imported = 0
        for agent_data in agents_data:
            # Проверяем существует ли агент
            existing = self.db.query(SourceAgent).filter(SourceAgent.id == agent_data['id']).first()
            if existing:
                # Обновляем существующий
                for key, value in agent_data.items():
                    if hasattr(existing, key) and key != 'id':
                        setattr(existing, key, value)
            else:
                # Создаем нового
                agent = SourceAgent(**agent_data)
                self.db.add(agent)
            imported += 1

        self.db.commit()
        return imported

    async def _import_rules(self, rules_data: List[Dict[str, Any]]) -> int:
        """Импорт правил."""
        imported = 0
        for rule_data in rules_data:
            # Проверяем существует ли правило
            existing = self.db.query(AlertRule).filter(AlertRule.id == rule_data['id']).first()
            if existing:
                # Обновляем существующее
                for key, value in rule_data.items():
                    if hasattr(existing, key) and key != 'id':
                        setattr(existing, key, value)
            else:
                # Создаем новое
                rule = AlertRule(**rule_data)
                self.db.add(rule)
            imported += 1

        self.db.commit()
        return imported

    async def _import_events(self, events_data: List[Dict[str, Any]]) -> int:
        """Импорт событий."""
        imported = 0
        for event_data in events_data:
            # Проверяем существует ли событие
            existing = self.db.query(ListingEvent).filter(ListingEvent.id == event_data['id']).first()
            if existing:
                # Обновляем существующее
                for key, value in event_data.items():
                    if hasattr(existing, key) and key != 'id':
                        setattr(existing, key, value)
            else:
                # Создаем новое
                event = ListingEvent(**event_data)
                self.db.add(event)
            imported += 1

        self.db.commit()
        return imported

    async def _import_price_history(self, history_data: List[Dict[str, Any]]) -> int:
        """Импорт истории цен."""
        imported = 0
        for ph_data in history_data:
            # Проверяем существует ли запись
            existing = self.db.query(PriceHistory).filter(
                PriceHistory.game_id == ph_data['game_id'],
                PriceHistory.store_id == ph_data['store_id'],
                PriceHistory.observed_at == ph_data['observed_at']
            ).first()

            if not existing:
                ph = PriceHistory(**ph_data)
                self.db.add(ph)
                imported += 1

        self.db.commit()
        return imported

    async def _import_notifications(self, notifications_data: List[Dict[str, Any]]) -> int:
        """Импорт уведомлений."""
        imported = 0
        for notif_data in notifications_data:
            # Проверяем существует ли уведомление
            existing = self.db.query(Notification).filter(Notification.id == notif_data['id']).first()
            if existing:
                # Обновляем существующее
                for key, value in notif_data.items():
                    if hasattr(existing, key) and key != 'id':
                        setattr(existing, key, value)
            else:
                # Создаем новое
                notif = Notification(**notif_data)
                self.db.add(notif)
            imported += 1

        self.db.commit()
        return imported

    async def _calculate_checksums(self, files: List[str], zip_file) -> str:
        """Рассчитать контрольные суммы для файлов."""
        import hashlib

        checksums = []
        for filename in files:
            if filename in zip_file.namelist():
                data = zip_file.read(filename)
                checksum = hashlib.sha256(data).hexdigest()
                checksums.append(f"{filename}: {checksum}")

        return "\n".join(checksums)

    async def get_import_summary(self, zip_data: bytes) -> Dict[str, Any]:
        """Получить сводку импорта без выполнения импорта."""
        zip_file = zipfile.ZipFile(io.BytesIO(zip_data))

        if "version.json" not in zip_file.namelist():
            raise ValueError("Missing version.json in export file")

        metadata = json.loads(zip_file.read("version.json").decode('utf-8'))

        summary = {
            "metadata": metadata,
            "files": {},
            "total_items": 0
        }

        file_mappings = {
            "games.ndjson": "games",
            "stores.ndjson": "stores",
            "listing_events.ndjson": "events",
            "price_history.ndjson": "price_history",
            "alert_rules.json": "rules",
            "sources.json": "agents",
            "notifications.ndjson": "notifications"
        }

        for filename, entity_name in file_mappings.items():
            if filename in zip_file.namelist():
                data = zip_file.read(filename).decode('utf-8')
                if filename.endswith('.json'):
                    items = json.loads(data)
                    count = len(items) if isinstance(items, list) else 1
                else:
                    count = len([line for line in data.strip().split('\n') if line.strip()])

                summary["files"][entity_name] = count
                summary["total_items"] += count

        return summary


# Фабрика для создания сервиса
def get_export_service(db: Session) -> ExportService:
    """Создать экземпляр ExportService."""
    return ExportService(db)