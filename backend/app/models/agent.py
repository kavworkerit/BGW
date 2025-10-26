from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class SourceAgent(Base):
    """Модель агента источника"""
    __tablename__ = "source_agent"

    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'api', 'html', 'headless', 'telegram_public'
    schedule = Column(JSON, nullable=False)
    rate_limit = Column(JSON, nullable=False)
    config = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<SourceAgent(id='{self.id}', name='{self.name}', type='{self.type}')>"