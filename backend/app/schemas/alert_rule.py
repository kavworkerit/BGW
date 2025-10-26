from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class LogicOperator(str, Enum):
    AND = "AND"
    OR = "OR"


class ComparisonOperator(str, Enum):
    IN = "in"
    CONTAINS = "contains"
    CONTAINS_ANY = "contains_any"
    GREATER_THAN_EQUAL = ">="
    LESS_THAN_EQUAL = "<="
    EQUALS = "="


class AlertCondition(BaseModel):
    """Условие правила"""
    field: str = Field(..., description="Поле для проверки")
    op: ComparisonOperator = Field(..., description="Оператор сравнения")
    value: Any = Field(..., description="Значение для сравнения")


class AlertRuleBase(BaseModel):
    """Базовая модель правила уведомлений"""
    name: str = Field(..., min_length=1, max_length=255)
    logic: LogicOperator = Field(default=LogicOperator.AND)
    conditions: List[AlertCondition] = Field(..., min_items=1)
    channels: List[str] = Field(..., min_items=1)
    cooldown_hours: int = Field(default=12, ge=1, le=168)  # от 1 часа до недели
    enabled: bool = Field(default=True)


class AlertRuleCreate(AlertRuleBase):
    """Модель для создания правила"""
    pass


class AlertRuleUpdate(BaseModel):
    """Модель для обновления правила"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    logic: Optional[LogicOperator] = None
    conditions: Optional[List[AlertCondition]] = Field(None, min_items=1)
    channels: Optional[List[str]] = Field(None, min_items=1)
    cooldown_hours: Optional[int] = Field(None, ge=1, le=168)
    enabled: Optional[bool] = None


class AlertRule(AlertRuleBase):
    """Полная модель правила уведомлений"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class AlertRuleResponse(AlertRule):
    """Модель ответа для правила уведомлений"""
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class RuleTestResult(BaseModel):
    """Результат тестирования правила"""
    rule_id: UUID
    matched_events: List[Dict[str, Any]]
    match_count: int
    sample_events: List[Dict[str, Any]]