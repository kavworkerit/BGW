from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class AlertRule(BaseModel):
    """Модель правил уведомлений"""
    __tablename__ = "alert_rule"

    name = Column(String(255), nullable=False)
    logic = Column(String(10), nullable=False, default="AND")  # 'AND' or 'OR'
    conditions = Column(JSON, nullable=False)
    channels = Column(JSON, nullable=False)  # ['webpush', 'telegram']
    cooldown_hours = Column(String(10), default="12")
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    notifications = relationship("Notification", back_populates="rule")

    def __repr__(self):
        return f"<AlertRule(id='{self.id}', name='{self.name}', enabled={self.enabled})>"