from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.models.base import Base


class PriceHistory(Base):
    """Модель истории цен (TimescaleDB hypertable)"""
    __tablename__ = "price_history"

    game_id = Column(UUID(as_uuid=True), ForeignKey("game.id"), primary_key=True)
    store_id = Column(String, ForeignKey("store.id"), primary_key=True)
    observed_at = Column(DateTime(timezone=True), primary_key=True, nullable=False)
    price = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="RUB")

    # Relationships
    game = relationship("Game", backref="price_history")
    store = relationship("Store", backref="price_history")

    def __repr__(self):
        return f"<PriceHistory(game_id='{self.game_id}', store_id='{self.store_id}', price={self.price})>"