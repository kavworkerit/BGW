from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class Notification(BaseModel):
    """Модель уведомлений"""
    __tablename__ = "notification"

    rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rule.id"), nullable=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey("listing_event.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # 'sent', 'error', 'deferred'
    sent_at = Column(DateTime(timezone=True))
    meta = Column(JSON, default={})  # Дополнительные метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    rule = relationship("AlertRule", back_populates="notifications")
    event = relationship("ListingEvent", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id='{self.id}', rule_id='{self.rule_id}', status='{self.status}')>"