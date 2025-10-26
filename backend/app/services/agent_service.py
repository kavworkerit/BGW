"""Сервис для управления агентами."""
import json
import zipfile
import io
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.agent import SourceAgent
from app.schemas.agent import SourceAgentCreate, SourceAgentUpdate
from app.agents.registry import agent_registry
from app.agents.base import RuntimeContext
from app.tasks.agents import run_agent_task


class AgentService:
    """Сервис для работы с агентами."""

    def __init__(self):
        self.registry = agent_registry

    async def get_agents(self, db: Session, skip: int = 0, limit: int = 100) -> List[SourceAgent]:
        """Получить список агентов."""
        return db.query(SourceAgent).offset(skip).limit(limit).all()

    async def get_agent(self, db: Session, agent_id: str) -> Optional[SourceAgent]:
        """Получить агента по ID."""
        return db.query(SourceAgent).filter(SourceAgent.id == agent_id).first()

    async def create_agent(self, db: Session, agent_data: SourceAgentCreate) -> SourceAgent:
        """Создать нового агента."""
        # Валидация конфигурации
        try:
            agent_class = self.registry.get(agent_data.type)
            # TODO: Validate config against schema
        except ValueError as e:
            raise ValueError(f"Invalid agent type: {e}")

        db_agent = SourceAgent(**agent_data.dict())
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        return db_agent

    async def update_agent(self, db: Session, agent_id: str, agent_data: SourceAgentUpdate) -> Optional[SourceAgent]:
        """Обновить агента."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            return None

        for field, value in agent_data.dict(exclude_unset=True).items():
            setattr(db_agent, field, value)

        db.commit()
        db.refresh(db_agent)
        return db_agent

    async def delete_agent(self, db: Session, agent_id: str) -> bool:
        """Удалить агента."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            return False

        db.delete(db_agent)
        db.commit()
        return True

    async def run_agent(self, db: Session, agent_id: str) -> dict:
        """Запустить агента."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            raise ValueError(f"Agent {agent_id} not found")

        if not db_agent.enabled:
            raise ValueError(f"Agent {agent_id} is disabled")

        # Запускаем задачу в Celery
        task = run_agent_task.delay(agent_id)

        return {
            "task_id": task.id,
            "status": "started",
            "agent_id": agent_id
        }

    async def import_agent(self, db: Session, file) -> SourceAgent:
        """Импортировать агента из ZIP файла."""
        # Читаем ZIP файл
        content = await file.read()
        zip_file = zipfile.ZipFile(io.BytesIO(content))

        # Читаем manifest.json
        try:
            manifest_data = zip_file.read('manifest.json').decode('utf-8')
            manifest = json.loads(manifest_data)
        except KeyError:
            raise ValueError("Missing manifest.json in ZIP file")

        # Валидация манифеста
        required_fields = ['id', 'name', 'type', 'entrypoint', 'schedule', 'rate_limit', 'config']
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field: {field}")

        # Создаем агента
        agent_data = SourceAgentCreate(
            id=manifest['id'],
            name=manifest['name'],
            type=manifest['type'],
            schedule=manifest['schedule'],
            rate_limit=manifest['rate_limit'],
            config=manifest['config'],
            enabled=True
        )

        # Проверяем что агент с таким ID еще не существует
        existing = await self.get_agent(db, manifest['id'])
        if existing:
            raise ValueError(f"Agent with ID {manifest['id']} already exists")

        return await self.create_agent(db, agent_data)

    async def export_agent(self, db: Session, agent_id: str) -> bytes:
        """Экспортировать агента в ZIP файл."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Создаем manifest
        manifest = {
            "version": "1.0",
            "id": db_agent.id,
            "name": db_agent.name,
            "type": db_agent.type,
            "entrypoint": "agent.py",
            "schedule": db_agent.schedule,
            "rate_limit": db_agent.rate_limit,
            "config": db_agent.config,
            "secrets": {}  # Секреты не экспортируем
        }

        # Создаем ZIP файл
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
            # TODO: Добавить код агента если он есть

        return zip_buffer.getvalue()


class AgentService:
    """Сервис для работы с агентами."""

    def __init__(self):
        self.registry = agent_registry

    async def get_agents(self, db: Session, skip: int = 0, limit: int = 100,
                        enabled_only: bool = False, agent_type: str = None) -> List[SourceAgent]:
        """Получить список агентов с фильтрацией."""
        query = db.query(SourceAgent)

        if enabled_only:
            query = query.filter(SourceAgent.enabled == True)

        if agent_type:
            query = query.filter(SourceAgent.type == agent_type)

        return query.offset(skip).limit(limit).all()

    async def get_agent(self, db: Session, agent_id: str) -> Optional[SourceAgent]:
        """Получить агента по ID."""
        return db.query(SourceAgent).filter(SourceAgent.id == agent_id).first()

    async def create_agent(self, db: Session, agent_data: SourceAgentCreate) -> SourceAgent:
        """Создать нового агента."""
        # Валидация конфигурации
        try:
            agent_class = self.registry.get(agent_data.type)
            # Валидация конфигурации через схему агента
            if hasattr(agent_class, 'CONFIG_SCHEMA'):
                self._validate_config(agent_data.config, agent_class.CONFIG_SCHEMA)
        except ValueError as e:
            raise ValueError(f"Invalid agent type: {e}")

        db_agent = SourceAgent(**agent_data.dict())
        db.add(db_agent)
        db.commit()
        db.refresh(db_agent)
        return db_agent

    async def update_agent(self, db: Session, agent_id: str, agent_data: SourceAgentUpdate) -> Optional[SourceAgent]:
        """Обновить агента."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            return None

        # Валидация типа если изменяется
        if 'type' in agent_data.dict(exclude_unset=True):
            try:
                agent_class = self.registry.get(agent_data.type)
                if hasattr(agent_class, 'CONFIG_SCHEMA'):
                    config = agent_data.config or db_agent.config
                    self._validate_config(config, agent_class.CONFIG_SCHEMA)
            except ValueError as e:
                raise ValueError(f"Invalid agent type: {e}")

        for field, value in agent_data.dict(exclude_unset=True).items():
            setattr(db_agent, field, value)

        db.commit()
        db.refresh(db_agent)
        return db_agent

    async def delete_agent(self, db: Session, agent_id: str) -> bool:
        """Удалить агента."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            return False

        # Проверяем связанные данные
        from app.models.raw_item import RawItem
        raw_items_count = db.query(RawItem).filter(RawItem.source_id == agent_id).count()
        if raw_items_count > 0:
            raise ValueError(f"Cannot delete agent with {raw_items_count} associated raw items")

        db.delete(db_agent)
        db.commit()
        return True

    async def run_agent(self, db: Session, agent_id: str) -> dict:
        """Запустить агента."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            raise ValueError(f"Agent {agent_id} not found")

        if not db_agent.enabled:
            raise ValueError(f"Agent {agent_id} is disabled")

        # Запускаем задачу в Celery
        task = run_agent_task.delay(agent_id)

        return {
            "task_id": task.id,
            "status": "started",
            "agent_id": agent_id,
            "started_at": datetime.utcnow().isoformat()
        }

    async def get_agent_stats(self, db: Session, agent_id: str, days: int = 30) -> dict:
        """Получить статистику агента."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            raise ValueError(f"Agent {agent_id} not found")

        from datetime import datetime, timedelta
        from app.models.raw_item import RawItem
        from app.models.listing_event import ListingEvent
        from sqlalchemy import func

        since_date = datetime.utcnow() - timedelta(days=days)

        # Статистика по raw items
        raw_items_query = db.query(
            func.count(RawItem.id).label('total'),
            func.count(func.distinct(RawItem.hash)).label('unique_pages')
        ).filter(
            RawItem.source_id == agent_id,
            RawItem.fetched_at >= since_date
        ).first()

        # Статистика по событиям
        events_stats = db.query(
            func.count(ListingEvent.id).label('total'),
            func.count(func.distinct(ListingEvent.game_id)).label('unique_games')
        ).filter(
            ListingEvent.source_id == agent_id,
            ListingEvent.created_at >= since_date
        ).first()

        # Последний запуск
        last_run = db.query(RawItem.fetched_at)\
            .filter(RawItem.source_id == agent_id)\
            .order_by(RawItem.fetched_at.desc())\
            .first()

        # Статистика по ошибкам (если есть)
        error_count = db.query(RawItem)\
            .filter(RawItem.source_id == agent_id)\
            .filter(RawItem.fetched_at >= since_date)\
            .count() - (raw_items_query.unique_pages if raw_items_query else 0)

        return {
            "agent_id": agent_id,
            "agent_name": db_agent.name,
            "agent_type": db_agent.type,
            "enabled": db_agent.enabled,
            "stats_period_days": days,
            "pages_fetched": raw_items_query.total if raw_items_query else 0,
            "unique_pages": raw_items_query.unique_pages if raw_items_query else 0,
            "events_created": events_stats.total if events_stats else 0,
            "unique_games_matched": events_stats.unique_games if events_stats else 0,
            "last_run": last_run.fetched_at.isoformat() if last_run else None,
            "success_rate": round(
                (raw_items_query.unique_pages / max(raw_items_query.total, 1)) * 100, 1
            ) if raw_items_query else 0,
            "daily_average": round(
                (raw_items_query.total / max(days, 1)), 1
            ) if raw_items_query else 0
        }

    async def get_agent_logs(self, db: Session, agent_id: str, limit: int = 100) -> List[dict]:
        """Получить логи работы агента."""
        # В реальной системе это могло бы быть связано с системой логирования
        # Пока возвращаем статистику recent runs
        from app.models.raw_item import RawItem
        from datetime import datetime, timedelta

        since_date = datetime.utcnow() - timedelta(days=7)

        recent_items = db.query(RawItem)\
            .filter(RawItem.source_id == agent_id)\
            .filter(RawItem.fetched_at >= since_date)\
            .order_by(RawItem.fetched_at.desc())\
            .limit(limit)\
            .all()

        logs = []
        for item in recent_items:
            logs.append({
                "timestamp": item.fetched_at.isoformat(),
                "url": item.url,
                "hash": item.hash[:16] + "...",
                "status": "success" if item.content_ref else "error",
                "content_size": len(item.content_ref) if item.content_ref else 0
            })

        return logs

    async def import_agent(self, db: Session, file) -> SourceAgent:
        """Импортировать агента из ZIP файла."""
        # Читаем ZIP файл
        content = await file.read()
        zip_file = zipfile.ZipFile(io.BytesIO(content))

        # Читаем manifest.json
        try:
            manifest_data = zip_file.read('manifest.json').decode('utf-8')
            manifest = json.loads(manifest_data)
        except KeyError:
            raise ValueError("Missing manifest.json in ZIP file")

        # Валидация манифеста
        required_fields = ['id', 'name', 'type', 'entrypoint', 'schedule', 'rate_limit', 'config']
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Missing required field: {field}")

        # Валидация типа агента
        if manifest['type'] not in self.registry.list_types():
            raise ValueError(f"Unsupported agent type: {manifest['type']}")

        # Создаем агента
        agent_data = SourceAgentCreate(
            id=manifest['id'],
            name=manifest['name'],
            type=manifest['type'],
            schedule=manifest['schedule'],
            rate_limit=manifest['rate_limit'],
            config=manifest['config'],
            enabled=True
        )

        # Проверяем что агент с таким ID еще не существует
        existing = await self.get_agent(db, manifest['id'])
        if existing:
            raise ValueError(f"Agent with ID {manifest['id']} already exists")

        return await self.create_agent(db, agent_data)

    async def export_agent(self, db: Session, agent_id: str) -> bytes:
        """Экспортировать агента в ZIP файл."""
        db_agent = await self.get_agent(db, agent_id)
        if not db_agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Создаем manifest
        manifest = {
            "version": "1.0",
            "id": db_agent.id,
            "name": db_agent.name,
            "type": db_agent.type,
            "entrypoint": "agent.py",
            "schedule": db_agent.schedule,
            "rate_limit": db_agent.rate_limit,
            "config": db_agent.config,
            "secrets": {},  # Секреты не экспортируем
            "created_at": db_agent.created_at.isoformat() if db_agent.created_at else None
        }

        # Создаем ZIP файл
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr('manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False))
            # TODO: Добавить код агента если он есть

        return zip_buffer.getvalue()

    async def get_available_agent_types(self) -> List[dict]:
        """Получить список доступных типов агентов."""
        types = []
        for agent_type in self.registry.list_types():
            agent_class = self.registry.get(agent_type)
            type_info = {
                "type": agent_type,
                "name": getattr(agent_class, 'NAME', agent_type.title()),
                "description": getattr(agent_class, 'DESCRIPTION', ''),
                "config_schema": getattr(agent_class, 'CONFIG_SCHEMA', {})
            }
            types.append(type_info)
        return types

    def _validate_config(self, config: dict, schema: dict) -> None:
        """Валидация конфигурации по JSON схеме."""
        # Простая валидация - в реальной системе использовать jsonschema
        required_fields = schema.get('required', [])
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: {field}")

        properties = schema.get('properties', {})
        for field, value in config.items():
            if field in properties:
                field_schema = properties[field]
                field_type = field_schema.get('type')

                if field_type == 'string' and not isinstance(value, str):
                    raise ValueError(f"Field {field} must be a string")
                elif field_type == 'number' and not isinstance(value, (int, float)):
                    raise ValueError(f"Field {field} must be a number")
                elif field_type == 'boolean' and not isinstance(value, bool):
                    raise ValueError(f"Field {field} must be a boolean")
                elif field_type == 'array' and not isinstance(value, list):
                    raise ValueError(f"Field {field} must be an array")


agent_service = AgentService()