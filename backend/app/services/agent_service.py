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


agent_service = AgentService()