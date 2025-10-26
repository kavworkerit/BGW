from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List, Optional, Dict, Any
from uuid import UUID
from app.core.database import get_db
from app.models.game import Game
from app.models.listing_event import ListingEvent
from app.schemas.game import Game as GameSchema, GameCreate, GameUpdate
from app.crud.game import game_crud
from app.services.game_matching_service import game_matching_service
from app.utils.pagination import PaginatedResponse, get_pagination_params, PaginationHelper
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_game_id(game_id: str) -> UUID:
    """Конвертирует строку game_id в UUID или выбрасывает исключение"""
    try:
        return UUID(game_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Некорректный ID игры")


@router.get("/", response_model=PaginatedResponse[GameSchema])
async def get_games(
    pagination: dict = Depends(get_pagination_params),
    search: Optional[str] = None,
    publisher: Optional[str] = None,
    min_players: Optional[int] = Query(None, ge=1),
    max_players: Optional[int] = Query(None, ge=1),
    min_playtime: Optional[int] = Query(None, ge=1),
    max_playtime: Optional[int] = Query(None, ge=1),
    tags: Optional[str] = None,  # comma-separated
    language: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Получить список игр с фильтрацией и пагинацией.

    Args:
        pagination: Параметры пагинации (skip, limit)
        search: Поиск по названию или синонимам
        publisher: Фильтр по издателю
        min_players: Минимальное количество игроков
        max_players: Максимальное количество игроков
        min_playtime: Минимальное время игры
        max_playtime: Максимальное время игры
        tags: Теги через запятую
        language: Язык игры (RU, EN)
        db: Сессия базы данных

    Returns:
        PaginatedResponse: Игры с мета-информацией о пагинации
    """
    query = db.query(Game)

    # Поиск по названию или синонимам
    if search:
        search_filter = or_(
            Game.title.ilike(f"%{search}%"),
            Game.synonyms.any(search)  # Это требует специального оператора для массивов
        )
        query = query.filter(search_filter)

    # Фильтр по издателю
    if publisher:
        query = query.filter(Game.publisher.ilike(f"%{publisher}%"))

    # Фильтры по количеству игроков
    if min_players:
        query = query.filter(Game.min_players >= min_players)
    if max_players:
        query = query.filter(Game.max_players <= max_players)

    # Фильтры по времени игры
    if min_playtime:
        query = query.filter(Game.min_playtime >= min_playtime)
    if max_playtime:
        query = query.filter(Game.max_playtime <= max_playtime)

    # Фильтр по тегам
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',')]
        for tag in tag_list:
            query = query.filter(Game.tags.any(tag))  # Это требует специального оператора

    # Фильтр по языку
    if language:
        query = query.filter(Game.language == language.upper())

    # Применяем пагинацию через утилиту
    items, total = PaginationHelper.get_paginated_results(
        query,
        skip=pagination.skip,
        limit=pagination.limit
    )

    return PaginatedResponse.create(
        items=items,
        total=total,
        skip=pagination.skip,
        limit=pagination.limit
    )


@router.post("/", response_model=GameSchema, status_code=201)
async def create_game(
    game: GameCreate,
    db: Session = Depends(get_db)
):
    """Создать новую игру."""
    # Проверка на дубликаты по BGG ID
    if game.bgg_id:
        existing = db.query(Game).filter(Game.bgg_id == game.bgg_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Игра с таким BGG ID уже существует")

    return game_crud.create(db, obj_in=game)


@router.get("/{game_id}", response_model=GameSchema)
async def get_game(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Получить игру по ID."""
    uuid_obj = parse_game_id(game_id)
    game = game_crud.get(db, uuid_obj)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")
    return game


@router.get("/{game_id}/events")
async def get_game_events(
    game_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    kind: Optional[str] = None,
    store_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Получить события для конкретной игры."""
    uuid_obj = parse_game_id(game_id)
    game = game_crud.get(db, uuid_obj)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    query = db.query(ListingEvent).filter(ListingEvent.game_id == uuid_obj)

    if kind:
        query = query.filter(ListingEvent.kind == kind)
    if store_id:
        query = query.filter(ListingEvent.store_id == store_id)

    events = query.order_by(ListingEvent.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": str(event.id),
            "kind": event.kind.value if event.kind else None,
            "title": event.title,
            "price": float(event.price) if event.price else None,
            "currency": event.currency,
            "discount_pct": float(event.discount_pct) if event.discount_pct else None,
            "in_stock": event.in_stock,
            "store_id": event.store_id,
            "url": event.url,
            "created_at": event.created_at
        }
        for event in events
    ]


@router.get("/{game_id}/price-history")
async def get_game_price_history(
    game_id: str,
    store_id: Optional[str] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Получить историю цен для игры."""
    uuid_obj = parse_game_id(game_id)
    game = game_crud.get(db, uuid_obj)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    from app.models.price_history import PriceHistory
    from datetime import datetime, timedelta

    since_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(PriceHistory).filter(
        and_(
            PriceHistory.game_id == uuid_obj,
            PriceHistory.observed_at >= since_date
        )
    )

    if store_id:
        query = query.filter(PriceHistory.store_id == store_id)

    price_history = query.order_by(PriceHistory.observed_at.desc()).all()

    return [
        {
            "store_id": ph.store_id,
            "price": float(ph.price),
            "currency": ph.currency,
            "observed_at": ph.observed_at
        }
        for ph in price_history
    ]


@router.post("/match", response_model=List[GameSchema])
async def match_games(
    title: str,
    threshold: float = Query(0.75, ge=0.5, le=1.0),
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Найти подходящие игры по названию."""
    suggestions = await game_matching_service.create_suggestions(db, title, limit)
    return suggestions


@router.put("/{game_id}", response_model=GameSchema)
async def update_game(
    game_id: str,
    game_update: GameUpdate,
    db: Session = Depends(get_db)
):
    """Обновить игру."""
    uuid_obj = parse_game_id(game_id)
    game = game_crud.get(db, uuid_obj)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    # Проверка BGG ID при обновлении
    if game_update.bgg_id and game_update.bgg_id != game.bgg_id:
        existing = db.query(Game).filter(
            and_(Game.bgg_id == game_update.bgg_id, Game.id != game_id)
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Игра с таким BGG ID уже существует")

    return game_crud.update(db, db_obj=game, obj_in=game_update)


@router.delete("/{game_id}")
async def delete_game(
    game_id: str,
    db: Session = Depends(get_db)
):
    """Удалить игру."""
    uuid_obj = parse_game_id(game_id)
    game = game_crud.get(db, uuid_obj)
    if not game:
        raise HTTPException(status_code=404, detail="Игра не найдена")

    # Проверяем связанные события
    events_count = db.query(ListingEvent).filter(ListingEvent.game_id == uuid_obj).count()
    if events_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить игру, у которой есть {events_count} связанных событий"
        )

    game_crud.remove(db, id=uuid_obj)
    return {"message": "Игра удалена"}


@router.post("/batch", response_model=List[GameSchema])
async def create_games_batch(
    games: List[GameCreate],
    db: Session = Depends(get_db)
):
    """Создать несколько игр."""
    created_games = []
    errors = []

    for game_data in games:
        try:
            # Проверка на дубликаты
            if game_data.bgg_id:
                existing = db.query(Game).filter(Game.bgg_id == game_data.bgg_id).first()
                if existing:
                    errors.append(f"Игра {game_data.title} уже существует")
                    continue

            game = game_crud.create(db, obj_in=game_data)
            created_games.append(game)
        except Exception as e:
            errors.append(f"Ошибка при создании игры {game_data.title}: {str(e)}")

    if errors:
        logger.warning(f"Errors in batch creation: {errors}")

    return created_games


@router.get("/stats/summary")
async def get_games_stats(db: Session = Depends(get_db)):
    """Получить статистику по играм."""
    total_games = db.query(Game).count()

    # Игры с BGG ID
    bgg_games = db.query(Game).filter(Game.bgg_id.isnot(None)).count()

    # По издателям
    publishers = db.query(Game.publisher, db.func.count(Game.id))\
        .filter(Game.publisher.isnot(None))\
        .group_by(Game.publisher)\
        .order_by(db.func.count(Game.id).desc())\
        .limit(10)\
        .all()

    # По языкам
    languages = db.query(Game.language, db.func.count(Game.id))\
        .group_by(Game.language)\
        .order_by(db.func.count(Game.id).desc())\
        .all()

    return {
        "total_games": total_games,
        "bgg_linked_games": bgg_games,
        "bgg_coverage_percent": round(bgg_games / total_games * 100, 1) if total_games > 0 else 0,
        "top_publishers": [{"publisher": pub, "count": count} for pub, count in publishers],
        "languages": [{"language": lang, "count": count} for lang, count in languages]
    }