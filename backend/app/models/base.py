from sqlalchemy import Column, DateTime, String
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class UUIDMixin:
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BaseModel(Base, UUIDMixin, TimestampMixin):
    __abstract__ = True