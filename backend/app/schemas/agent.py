from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class SourceAgentBase(BaseModel):
    """Базовая модель агента источника"""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(api|html|headless|telegram_public)$")
    schedule: Dict[str, Any] = Field(..., description="Расписание запуска")
    rate_limit: Dict[str, Any] = Field(..., description="Ограничения частоты запросов")
    config: Dict[str, Any] = Field(..., description="Конфигурация агента")
    enabled: bool = Field(default=True)


class SourceAgentCreate(SourceAgentBase):
    """Модель для создания агента"""
    id: str = Field(..., min_length=1, max_length=100)


class SourceAgentUpdate(BaseModel):
    """Модель для обновления агента"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    type: Optional[str] = Field(None, pattern="^(api|html|headless|telegram_public)$")
    schedule: Optional[Dict[str, Any]] = None
    rate_limit: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None


class SourceAgent(SourceAgentBase):
    """Полная модель агента источника"""
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SourceAgentResponse(SourceAgent):
    """Модель ответа для агента источника"""
    last_run: Optional[datetime] = None
    status: Optional[str] = None
    next_run: Optional[datetime] = None
    pages_today: int = 0
    error_count: int = 0