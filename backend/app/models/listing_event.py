from sqlalchemy import Column, String, DateTime, Numeric, Boolean, Text, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import BaseModel
import enum


class EventKind(enum.Enum):
    ANNOUNCE = "announce"
    PREORDER = "preorder"
    RELEASE = "release"
    DISCOUNT = "discount"
    PRICE = "price"


class ListingEvent(BaseModel):
    __tablename__ = "listing_event"

    game_id = Column(String, ForeignKey("game.id"), nullable=True, index=True)
    store_id = Column(String, ForeignKey("store.id"), nullable=True, index=True)
    kind = Column(Enum(EventKind), nullable=False, index=True)
    title = Column(String(500), nullable=True)
    edition = Column(String(200), nullable=True)
    price = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), default="RUB")
    discount_pct = Column(Numeric(5, 2), nullable=True)
    in_stock = Column(Boolean, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    url = Column(Text, nullable=True)
    source_id = Column(String, ForeignKey("source_agent.id"), nullable=True)
    signature_hash = Column(String(64), nullable=False, unique=True, index=True)
    meta = Column(JSONB, default={})

    def __repr__(self):
        return f"<ListingEvent(title='{self.title}', kind='{self.kind.value}')>"