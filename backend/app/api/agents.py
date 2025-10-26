from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.schemas.agent import SourceAgent as SourceAgentSchema, SourceAgentCreate
from app.services.agent_service import agent_service

router = APIRouter()


@router.get("/", response_model=List[SourceAgentSchema])
async def get_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Получить список агентов."""
    return agent_service.get_agents(db, skip=skip, limit=limit)


@router.post("/", response_model=SourceAgentSchema)
async def create_agent(
    agent: SourceAgentCreate,
    db: Session = Depends(get_db)
):
    """Создать нового агента."""
    return agent_service.create_agent(db, agent)


@router.get("/{agent_id}", response_model=SourceAgentSchema)
async def get_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Получить агента по ID."""
    agent = agent_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")
    return agent


@router.post("/{agent_id}/run")
async def run_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Запустить агента вручную."""
    result = await agent_service.run_agent(db, agent_id)
    return {"message": "Агент запущен", "result": result}


@router.post("/import")
async def import_agent(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Импортировать агента из ZIP файла."""
    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате ZIP")

    result = await agent_service.import_agent(db, file)
    return {"message": "Агент импортирован", "agent": result}


@router.get("/{agent_id}/stats")
async def get_agent_stats(
    agent_id: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Получить статистику агента."""
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_
    from app.models.raw_item import RawItem
    from app.models.listing_event import ListingEvent

    # Проверяем существование агента
    agent = agent_service.get_agent(db, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Агент не найден")

    # Вычисляем дату начала периода
    since_date = datetime.utcnow() - timedelta(days=days)

    # Статистика по страницам
    pages_stats = db.query(RawItem).filter(
        and_(
            RawItem.source_id == agent_id,
            RawItem.fetched_at >= since_date
        )
    ).all()

    # Статистика по событиям
    events_stats = db.query(ListingEvent).filter(
        and_(
            ListingEvent.source_id == agent_id,
            ListingEvent.created_at >= since_date
        )
    ).all()

    # Последний запуск
    last_run = db.query(RawItem).filter(
        RawItem.source_id == agent_id
    ).order_by(RawItem.fetched_at.desc()).first()

    # Уникальные страницы (для расчета успешности)
    unique_pages = db.query(func.count(func.distinct(RawItem.hash))).filter(
        and_(
            RawItem.source_id == agent_id,
            RawItem.fetched_at >= since_date
        )
    ).scalar() or 0

    # Успешность в процентах
    success_rate = (unique_pages / max(len(pages_stats), 1)) * 100 if pages_stats else 100

    return {
        "agent_id": agent_id,
        "days": days,
        "last_run": last_run.fetched_at.isoformat() if last_run else None,
        "pages_fetched": len(pages_stats),
        "events_generated": len(events_stats),
        "unique_pages": unique_pages,
        "success_rate": round(success_rate, 1),
        "avg_pages_per_day": round(len(pages_stats) / days, 1) if days > 0 else 0,
        "avg_events_per_day": round(len(events_stats) / days, 1) if days > 0 else 0
    }


@router.get("/{agent_id}/export")
async def export_agent(
    agent_id: str,
    db: Session = Depends(get_db)
):
    """Экспортировать агента в ZIP файл."""
    zip_data = await agent_service.export_agent(db, agent_id)
    from fastapi.responses import StreamingResponse
    import io

    return StreamingResponse(
        io.BytesIO(zip_data),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={agent_id}.zip"}
    )