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