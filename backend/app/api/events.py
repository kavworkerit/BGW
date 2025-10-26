from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from app.schemas.listing_event import ListingEvent, ListingEventCreate, ListingEventResponse
from app.services.event_service import EventService
from app.core.database import get_db

router = APIRouter()


@router.get("/", response_model=List[ListingEventResponse])
async def get_events(
    game_id: Optional[UUID] = Query(None),
    store_id: Optional[str] = Query(None),
    kind: Optional[str] = Query(None),
    min_discount: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db=Depends(get_db)
):
    """Получить список событий с фильтрацией"""
    event_service = EventService(db)
    events = await event_service.get_events(
        game_id=game_id,
        store_id=store_id,
        kind=kind,
        min_discount=min_discount,
        max_price=max_price,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
        offset=offset
    )
    return events


@router.get("/{event_id}", response_model=ListingEventResponse)
async def get_event(event_id: UUID, db=Depends(get_db)):
    """Получить конкретное событие"""
    event_service = EventService(db)
    event = await event_service.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Событие не найдено")
    return event