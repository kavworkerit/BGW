from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class EventKind(str, Enum):
    ANNOUNCE = "announce"
    PREORDER = "preorder"
    RELEASE = "release"
    DISCOUNT = "discount"
    PRICE = "price"


class ListingEventBase(BaseModel):
    """Базовая модель события листинга"""
    game_id: Optional[UUID] = None
    store_id: Optional[str] = None
    kind: Optional[EventKind] = None
    title: Optional[str] = None
    edition: Optional[str] = None
    price: Optional[float] = None
    currency: str = "RUB"
    discount_pct: Optional[float] = None
    in_stock: Optional[bool] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    url: Optional[str] = None
    source_id: Optional[str] = None


class ListingEventCreate(ListingEventBase):
    """Модель для создания события"""
    pass


class ListingEventUpdate(ListingEventBase):
    """Модель для обновления события"""
    pass


class ListingEvent(ListingEventBase):
    """Полная модель события листинга"""
    id: UUID
    signature_hash: str
    created_at: datetime

    class Config:
        from_attributes = True


class ListingEventResponse(ListingEvent):
    """Модель ответа для события листинга"""
    game_title: Optional[str] = None
    store_name: Optional[str] = None
    processed: bool = False


class ListingEventDraft(BaseModel):
    """Черновик события листинга (без game_id)"""
    title: str
    store_id: Optional[str] = None
    kind: Optional[EventKind] = None
    price: Optional[float] = None
    discount_pct: Optional[float] = None
    edition: Optional[str] = None
    in_stock: Optional[bool] = None
    url: Optional[str] = None
    source_id: str