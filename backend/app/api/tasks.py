from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.celery_app import celery_app

router = APIRouter()


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Получить статус задачи Celery."""
    try:
        # Получаем результат задачи из Celery
        task = celery_app.AsyncResult(task_id)

        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'current': 0,
                'total': 1,
                'status': 'Pending...'
            }
        elif task.state != 'FAILURE':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'status': task.info.get('status', '')
            }
            if 'result' in task.info:
                response['result'] = task.info['result']
        else:
            # задача не удалась
            response = {
                'state': task.state,
                'current': 1,
                'total': 1,
                'status': str(task.info)  # исключение
            }

        return response
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@router.get("/")
async def list_tasks(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Получить список задач (ограниченная реализация)."""
    # В реальной реализации здесь был бы запрос к базе данных
    # для хранения истории задач
    return {
        "tasks": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    }


@router.delete("/{task_id}")
async def cancel_task(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Отменить задачу."""
    try:
        celery_app.control.revoke(task_id, terminate=True)
        return {"message": f"Task {task_id} revoked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke task {task_id}")