from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from .base import BaseModel


class RawItem(BaseModel):
    """Модель сырых данных от агента"""
    __tablename__ = "raw_item"

    source_id = Column(String, ForeignKey("source_agent.id"), nullable=False)
    url = Column(Text)
    fetched_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    content_ref = Column(String(255), nullable=False)  # S3 key

    # Relationships
    source_agent = relationship("SourceAgent", backref="raw_items")

    def __repr__(self):
        return f"<RawItem(id='{self.id}', source_id='{self.source_id}', hash='{self.hash[:16]}...')>"