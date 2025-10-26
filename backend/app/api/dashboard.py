from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from app.core.database import get_db
from app.models.game import Game
from app.models.store import Store
from app.models.listing_event import ListingEvent
from app.models.agent import SourceAgent
from app.models.raw_item import RawItem
from app.models.alert_rule import AlertRule

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Получить статистику для дашборда."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Общие статистики
    total_games = db.query(Game).count()
    total_stores = db.query(Store).count()
    total_agents = db.query(SourceAgent).count()
    total_rules = db.query(AlertRule).count()

    # Активные сущности
    active_agents = db.query(SourceAgent).filter(SourceAgent.enabled == True).count()
    active_rules = db.query(AlertRule).filter(AlertRule.enabled == True).count()

    # Статистика за сегодня
    today_events = db.query(ListingEvent).filter(ListingEvent.created_at >= today_start).count()
    today_pages = db.query(RawItem).filter(RawItem.fetched_at >= today_start).count()

    # Успешность (процент уникальных страниц от общего числа)
    last_24h = now - timedelta(hours=24)
    total_pages_24h = db.query(RawItem).filter(RawItem.fetched_at >= last_24h).count()
    unique_pages_24h = db.query(func.count(func.distinct(RawItem.hash)))\
        .filter(RawItem.fetched_at >= last_24h)\
        .scalar() or 0

    success_rate = (unique_pages_24h / max(total_pages_24h, 1)) * 100 if total_pages_24h > 0 else 100

    return {
        "total_games": total_games,
        "total_stores": total_stores,
        "total_agents": total_agents,
        "total_rules": total_rules,
        "active_agents": active_agents,
        "active_rules": active_rules,
        "today_events": today_events,
        "today_pages": today_pages,
        "success_rate": round(success_rate, 1)
    }


@router.get("/activity")
async def get_activity_feed(
    hours: int = 24,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Получить ленту активности."""
    since_date = datetime.utcnow() - timedelta(hours=hours)

    # Получаем события
    events = db.query(ListingEvent)\
        .filter(ListingEvent.created_at >= since_date)\
        .order_by(ListingEvent.created_at.desc())\
        .limit(limit)\
        .all()

    activity = []
    for event in events:
        activity.append({
            "id": str(event.id),
            "type": "event",
            "title": f"{event.title} - {event.kind.value}",
            "description": f"Магазин: {event.store_id}, Цена: {event.price}₽" if event.price else f"Магазин: {event.store_id}",
            "timestamp": event.created_at.isoformat(),
            "entity_id": str(event.id),
            "details": {
                "store_id": event.store_id,
                "kind": event.kind.value,
                "price": float(event.price) if event.price else None,
                "discount_pct": float(event.discount_pct) if event.discount_pct else None
            }
        })

    # Получаем запуски агентов
    agent_runs = db.query(RawItem)\
        .filter(RawItem.fetched_at >= since_date)\
        .order_by(RawItem.fetched_at.desc())\
        .limit(limit // 2)\
        .all()

    for run in agent_runs:
        agent = db.query(SourceAgent).filter(SourceAgent.id == run.source_id).first()
        if agent:
            activity.append({
                "id": str(run.id),
                "type": "agent_run",
                "title": f"Запуск агента: {agent.name}",
                "description": f"URL: {run.url[:50]}{'...' if len(run.url) > 50 else ''}",
                "timestamp": run.fetched_at.isoformat(),
                "entity_id": str(agent.id),
                "details": {
                    "agent_type": agent.type,
                    "url": run.url,
                    "hash": run.hash[:16] + "..."
                }
            })

    # Сортируем по времени
    activity.sort(key=lambda x: x["timestamp"], reverse=True)
    return activity[:limit]


@router.get("/system-health")
async def get_system_health(db: Session = Depends(get_db)):
    """Получить информацию о здоровье системы."""
    now = datetime.utcnow()

    # Проверяем активность агентов
    active_agents = db.query(SourceAgent).filter(SourceAgent.enabled == True).all()
    last_24h = now - timedelta(hours=24)

    agent_health = []
    for agent in active_agents:
        last_run = db.query(RawItem)\
            .filter(RawItem.source_id == agent.id)\
            .filter(RawItem.fetched_at >= last_24h)\
            .order_by(RawItem.fetched_at.desc())\
            .first()

        status = "healthy"
        if not last_run:
            status = "no_runs"
        elif (now - last_run.fetched_at).total_seconds() > 86400:  # Больше 24 часов
            status = "stale"

        agent_health.append({
            "id": agent.id,
            "name": agent.name,
            "type": agent.type,
            "status": status,
            "last_run": last_run.fetched_at.isoformat() if last_run else None
        })

    # Проверяем ошибки за последние 24 часа
    error_events = db.query(ListingEvent)\
        .filter(and_(
            ListingEvent.created_at >= last_24h,
            ListingEvent.meta.contains('error')
        ))\
        .count()

    # Общая статистика
    health_score = 100
    if error_events > 0:
        health_score -= min(error_events * 5, 30)
    if any(a["status"] != "healthy" for a in agent_health):
        health_score -= min(len([a for a in agent_health if a["status"] != "healthy"]) * 10, 40)

    return {
        "health_score": max(health_score, 0),
        "agent_health": agent_health,
        "error_events_24h": error_events,
        "last_check": now.isoformat(),
        "issues": [
            *[f"Agent {a['name']} hasn't run in over 24h" for a in agent_health if a["status"] == "stale"],
            *[f"Agent {a['name']} hasn't run yet" for a in agent_health if a["status"] == "no_runs"],
        ] if error_events > 0 else [f"{error_events} error events in last 24h"]
    }


@router.get("/performance-metrics")
async def get_performance_metrics(db: Session = Depends(get_db)):
    """Получить метрики производительности."""
    now = datetime.utcnow()
    last_24h = now - timedelta(hours=24)
    last_7d = now - timedelta(days=7)

    # Производительность агентов за последние 24 часа
    agent_metrics = []
    agents = db.query(SourceAgent).filter(SourceAgent.enabled == True).all()

    for agent in agents:
        # Статистика за 24 часа
        runs_24h = db.query(RawItem)\
            .filter(and_(
                RawItem.source_id == agent.id,
                RawItem.fetched_at >= last_24h
            )).all()

        runs_7d = db.query(RawItem)\
            .filter(and_(
                RawItem.source_id == agent.id,
                RawItem.fetched_at >= last_7d
            )).all()

        events_24h = db.query(ListingEvent)\
            .filter(and_(
                ListingEvent.source_id == agent.id,
                ListingEvent.created_at >= last_24h
            )).count()

        unique_pages_24h = db.query(func.count(func.distinct(RawItem.hash)))\
            .filter(and_(
                RawItem.source_id == agent.id,
                RawItem.fetched_at >= last_24h
            )).scalar() or 0

        avg_run_time = 0  # В реальной системе здесь будет замер времени выполнения
        if runs_24h:
            time_diffs = []
            for i in range(1, len(runs_24h)):
                diff = (runs_24h[i-1].fetched_at - runs_24h[i].fetched_at).total_seconds()
                time_diffs.append(diff)
            avg_run_time = sum(time_diffs) / len(time_diffs) if time_diffs else 0

        agent_metrics.append({
            "id": agent.id,
            "name": agent.name,
            "type": agent.type,
            "runs_24h": len(runs_24h),
            "runs_7d": len(runs_7d),
            "events_24h": events_24h,
            "unique_pages_24h": unique_pages_24h,
            "success_rate": (unique_pages_24h / max(len(runs_24h), 1)) * 100 if runs_24h else 0,
            "avg_run_time_seconds": round(avg_run_time, 2),
            "pages_per_hour": len(runs_24h) / 24 if runs_24h else 0
        })

    return {
        "agent_metrics": agent_metrics,
        "total_runs_24h": sum(m["runs_24h"] for m in agent_metrics),
        "total_events_24h": sum(m["events_24h"] for m in agent_metrics),
        "avg_success_rate": sum(m["success_rate"] for m in agent_metrics) / max(len(agent_metrics), 1),
        "calculated_at": now.isoformat()
    }