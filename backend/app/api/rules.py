from fastapi import APIRouter, Depends, HTTPException
from typing import List
from uuid import UUID

from app.schemas.alert_rule import AlertRule, AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse
from app.services.notification_service import NotificationService
from app.core.database import get_db

router = APIRouter()


@router.get("/", response_model=List[AlertRuleResponse])
async def get_rules(db=Depends(get_db)):
    """Получить список правил уведомлений"""
    notification_service = NotificationService(db)
    rules = await notification_service.get_all_rules()
    return rules


@router.post("/", response_model=AlertRuleResponse)
async def create_rule(rule: AlertRuleCreate, db=Depends(get_db)):
    """Создать новое правило уведомлений"""
    notification_service = NotificationService(db)
    created_rule = await notification_service.create_rule(rule)
    return created_rule


@router.put("/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(rule_id: UUID, rule: AlertRuleUpdate, db=Depends(get_db)):
    """Обновить правило уведомлений"""
    notification_service = NotificationService(db)
    updated_rule = await notification_service.update_rule(rule_id, rule)
    if not updated_rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    return updated_rule


@router.delete("/{rule_id}")
async def delete_rule(rule_id: UUID, db=Depends(get_db)):
    """Удалить правило уведомлений"""
    notification_service = NotificationService(db)
    success = await notification_service.delete_rule(rule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    return {"message": "Правило удалено"}


@router.post("/{rule_id}/test")
async def test_rule(rule_id: UUID, db=Depends(get_db)):
    """Протестировать правило на последних событиях"""
    notification_service = NotificationService(db)
    test_results = await notification_service.test_rule(rule_id)
    return test_results