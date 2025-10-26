"""Задачи для выполнения агентов."""
from celery import current_task
from app.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.agent import SourceAgent
from app.agents.registry import agent_registry
from app.agents.base import RuntimeContext
from app.services.notification_service import get_notification_service
from app.services.event_service import event_service
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def run_agent_task(self, agent_id: str):
    """Запустить агента."""
    import asyncio
    from app.services.event_service import event_service

    db = SessionLocal()
    try:
        # Получаем агента из базы
        agent = db.query(SourceAgent).filter(SourceAgent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        if not agent.enabled:
            logger.warning(f"Agent {agent_id} is disabled")
            return {"status": "skipped", "reason": "disabled"}

        # Обновляем статус задачи
        if current_task:
            current_task.update_state(
                state='PROGRESS',
                meta={'status': 'running', 'agent_id': agent_id}
            )

        # Получаем класс агента
        try:
            agent_class = agent_registry.get(agent.type)
        except ValueError as e:
            logger.error(f"Unknown agent type: {e}")
            return {"status": "error", "reason": f"Unknown agent type: {agent.type}"}

        # Создаем контекст выполнения
        ctx = RuntimeContext(
            agent_id=agent.id,
            config=agent.config,
            secrets={}  # Секреты получаем из безопасного хранилища
        )

        # Запускаем агента
        try:
            # Запускаем асинхронный код в event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            events = loop.run_until_complete(agent_class(agent.config, {}, ctx).run())
            loop.close()

            logger.info(f"Agent {agent_id} found {len(events)} events")

            # Обрабатываем найденные события
            processed_count = 0
            for event_draft in events:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    event = loop.run_until_complete(event_service.process_event(db, event_draft, agent.id))

                    if event:
                        processed_count += 1

                        # Проверяем правила уведомлений
                        loop.run_until_complete(event_service.check_notification_rules(db, event))

                    loop.close()

                except Exception as e:
                    logger.error(f"Error processing event: {e}")

            result = {
                "status": "completed",
                "agent_id": agent_id,
                "events_found": len(events),
                "events_processed": processed_count
            }

        except Exception as e:
            logger.error(f"Agent {agent_id} execution failed: {e}")
            result = {
                "status": "error",
                "agent_id": agent_id,
                "error": str(e)
            }

        return result

    finally:
        db.close()


@celery_app.task
def schedule_all_agents():
    """Запустить все активные агенты по расписанию."""
    db = SessionLocal()
    try:
        agents = db.query(SourceAgent).filter(SourceAgent.enabled == True).all()

        for agent in agents:
            try:
                run_agent_task.delay(agent.id)
                logger.info(f"Scheduled agent {agent.id}")
            except Exception as e:
                logger.error(f"Failed to schedule agent {agent.id}: {e}")

        return {"status": "completed", "agents_scheduled": len(agents)}

    finally:
        db.close()