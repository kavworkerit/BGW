from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text
from sqlalchemy.sql import func
import uuid

from .base import BaseModel


class SourceAgent(BaseModel):
    """Модель агента источника"""
    __tablename__ = "source_agent"

    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # 'api', 'html', 'headless', 'telegram_public'
    schedule = Column(JSON, nullable=False)
    rate_limit = Column(JSON, nullable=False)
    config = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True)

    def __repr__(self):
        return f"<SourceAgent(id='{self.id}', name='{self.name}', type='{self.type}')>"