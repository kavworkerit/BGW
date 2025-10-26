from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class NotificationStatus(str, Enum):
    SENT = "sent"
    ERROR = "error"
    DEFERRED = "deferred"
    PENDING = "pending"


class NotificationChannel(str, Enum):
    WEBPUSH = "webpush"
    TELEGRAM = "telegram"
    EMAIL = "email"


class NotificationBase(BaseModel):
    """Базовая модель уведомления"""
    rule_id: UUID
    event_id: UUID
    status: NotificationStatus = NotificationStatus.PENDING
    sent_at: Optional[datetime] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class NotificationCreate(NotificationBase):
    """Модель для создания уведомления"""
    pass


class Notification(NotificationBase):
    """Полная модель уведомления"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationResponse(Notification):
    """Модель ответа для уведомления"""
    rule_name: Optional[str] = None
    event_title: Optional[str] = None
    event_store: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0


class NotificationTemplate(BaseModel):
    """Шаблон уведомления"""
    title: str
    body: str
    icon: Optional[str] = None
    url: Optional[str] = None
    actions: Optional[Dict[str, str]] = None


class WebPushSubscription(BaseModel):
    """Подписка на Web Push"""
    endpoint: str
    keys: Dict[str, str]
    user_agent: Optional[str] = None


class NotificationStats(BaseModel):
    """Статистика уведомлений"""
    total: int
    sent: int
    errors: int
    pending: int
    by_channel: Dict[str, int]