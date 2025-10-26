from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.services.export_service import get_export_service
import io

router = APIRouter()


@router.get("/full")
async def export_full(
    include_raw_data: bool = Query(False, description="Include raw data"),
    db: Session = Depends(get_db)
):
    """Полный экспорт всех данных в ZIP архиве."""
    export_service = get_export_service(db)

    try:
        zip_data = await export_service.export_full(include_raw_data=include_raw_data)

        # Создаем streaming response
        def iterfile():
            yield zip_data

        return StreamingResponse(
            io.BytesIO(zip_data),
            media_type="application/zip",
            headers={
                "Content-Disposition": "attachment; filename=bgw_export.zip"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.post("/full")
async def import_full(
    file: UploadFile = File(..., description="ZIP файл с данными для импорта"),
    dry_run: bool = Query(True, description="Просмотр изменений без применения"),
    db: Session = Depends(get_db)
):
    """Полный импорт данных из ZIP архива."""
    export_service = get_export_service(db)

    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")

    try:
        zip_data = await file.read()
        result = await export_service.import_full(zip_data, dry_run=dry_run)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


@router.post("/summary")
async def get_import_summary(
    file: UploadFile = File(..., description="ZIP файл для анализа"),
    db: Session = Depends(get_db)
):
    """Получить сводку импорта без выполнения."""
    export_service = get_export_service(db)

    if not file.filename.endswith('.zip'):
        raise HTTPException(status_code=400, detail="File must be a ZIP archive")

    try:
        zip_data = await file.read()
        summary = await export_service.get_import_summary(zip_data)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/games/csv")
async def export_games_csv(
    game_ids: Optional[str] = Query(None, description="ID игр через запятую"),
    db: Session = Depends(get_db)
):
    """Экспорт игр в CSV формате."""
    export_service = get_export_service(db)

    try:
        game_ids_list = None
        if game_ids:
            game_ids_list = [id.strip() for id in game_ids.split(',') if id.strip()]

        csv_data = await export_service.export_games_csv(game_ids_list)

        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=games_export.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV export failed: {str(e)}")


@router.get("/price-history/{game_id}/csv")
async def export_price_history_csv(
    game_id: str,
    days: int = Query(365, ge=1, le=3650, description="Период в днях"),
    db: Session = Depends(get_db)
):
    """Экспорт истории цен игры в CSV формате."""
    export_service = get_export_service(db)

    try:
        csv_data = await export_service.export_price_history_csv(game_id, days)

        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=price_history_{game_id}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Price history export failed: {str(e)}")


@router.get("/events/csv")
async def export_events_csv(
    game_ids: Optional[str] = Query(None, description="ID игр через запятую"),
    store_ids: Optional[str] = Query(None, description="ID магазинов через запятую"),
    kinds: Optional[str] = Query(None, description="Типы событий через запятую"),
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    db: Session = Depends(get_db)
):
    """Экспорт событий в CSV формате."""
    export_service = get_export_service(db)

    try:
        # Парсинг параметров
        game_ids_list = None
        if game_ids:
            game_ids_list = [id.strip() for id in game_ids.split(',') if id.strip()]

        store_ids_list = None
        if store_ids:
            store_ids_list = [id.strip() for id in store_ids.split(',') if id.strip()]

        kinds_list = None
        if kinds:
            kinds_list = [kind.strip() for kind in kinds.split(',') if kind.strip()]

        csv_data = await export_service.export_events_csv(
            game_ids=game_ids_list,
            store_ids=store_ids_list,
            kinds=kinds_list,
            days=days
        )

        filename = f"events_export_{datetime.now().strftime('%Y%m%d')}.csv"
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Events export failed: {str(e)}")


@router.get("/agents/json")
async def export_agents_json(
    agent_ids: Optional[str] = Query(None, description="ID агентов через запятую"),
    include_secrets: bool = Query(False, description="Включить секреты в экспорт"),
    db: Session = Depends(get_db)
):
    """Экспорт конфигураций агентов в JSON формате."""
    export_service = get_export_service(db)

    try:
        agent_ids_list = None
        if agent_ids:
            agent_ids_list = [id.strip() for id in agent_ids.split(',') if id.strip()]

        json_data = await export_service.export_agents_json(
            agent_ids=agent_ids_list,
            include_secrets=include_secrets
        )

        filename = f"agents_export_{datetime.now().strftime('%Y%m%d')}.json"
        return StreamingResponse(
            io.StringIO(json_data),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agents export failed: {str(e)}")


@router.get("/rules/json")
async def export_rules_json(
    rule_ids: Optional[str] = Query(None, description="ID правил через запятую"),
    db: Session = Depends(get_db)
):
    """Экспорт правил уведомлений в JSON формате."""
    export_service = get_export_service(db)

    try:
        rule_ids_list = None
        if rule_ids:
            rule_ids_list = [id.strip() for id in rule_ids.split(',') if id.strip()]

        json_data = await export_service.export_rules_json(rule_ids=rule_ids_list)

        filename = f"rules_export_{datetime.now().strftime('%Y%m%d')}.json"
        return StreamingResponse(
            io.StringIO(json_data),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rules export failed: {str(e)}")


@router.get("/backup/schedule")
async def get_backup_schedule(db: Session = Depends(get_db)):
    """Получить расписание автоматических бэкапов."""
    export_service = get_export_service(db)

    try:
        schedule = await export_service.get_backup_schedule()
        return {"schedule": schedule}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get backup schedule: {str(e)}")


@router.post("/backup/schedule")
async def update_backup_schedule(
    enabled: bool = Query(..., description="Включить расписание"),
    time: str = Query(..., description="Время бэкапа в формате HH:MM"),
    days: Optional[str] = Query(None, description="Дни недели через запятую (0-6)"),
    retention_days: int = Query(30, ge=1, le=365, description="Дней хранения бэкапов"),
    db: Session = Depends(get_db)
):
    """Обновить расписание автоматических бэкапов."""
    export_service = get_export_service(db)

    try:
        days_list = None
        if days:
            days_list = [int(day.strip()) for day in days.split(',') if day.strip()]
            for day in days_list:
                if day < 0 or day > 6:
                    raise HTTPException(status_code=400, detail="Days must be 0-6 (Sunday=0)")

        schedule = await export_service.update_backup_schedule(
            enabled=enabled,
            time=time,
            days=days_list,
            retention_days=retention_days
        )

        return {"schedule": schedule, "message": "Backup schedule updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update backup schedule: {str(e)}")


@router.get("/backup/list")
async def list_backups(
    limit: int = Query(10, ge=1, le=100, description="Лимит записей"),
    db: Session = Depends(get_db)
):
    """Получить список доступных бэкапов."""
    export_service = get_export_service(db)

    try:
        backups = await export_service.list_backups(limit=limit)
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.post("/backup/{backup_id}/restore")
async def restore_from_backup(
    backup_id: str,
    dry_run: bool = Query(True, description="Просмотр изменений без применения"),
    db: Session = Depends(get_db)
):
    """Восстановление из бэкапа."""
    export_service = get_export_service(db)

    try:
        result = await export_service.restore_from_backup(backup_id, dry_run=dry_run)
        return result
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete("/backup/{backup_id}")
async def delete_backup(
    backup_id: str,
    db: Session = Depends(get_db)
):
    """Удаление бэкапа."""
    export_service = get_export_service(db)

    try:
        await export_service.delete_backup(backup_id)
        return {"message": f"Backup {backup_id} deleted successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Backup not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete backup: {str(e)}")