"""API эндпоинты для аналитики."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.models.game import Game
from app.models.store import Store
from app.models.listing_event import ListingEvent
from app.models.price_history import PriceHistory
from app.models.agent import SourceAgent

router = APIRouter()


@router.get("/overview")
async def get_analytics_overview(
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    db: Session = Depends(get_db)
):
    """Получить общую аналитику по системе."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Общая статистика
    total_games = db.query(Game).count()
    total_stores = db.query(Store).count()
    total_agents = db.query(SourceAgent).count()
    active_agents = db.query(SourceAgent).filter(SourceAgent.enabled == True).count()

    # Статистика за период
    events_in_period = db.query(ListingEvent).filter(
        ListingEvent.created_at >= start_date
    ).count()

    # Средняя цена
    avg_price_result = db.query(func.avg(ListingEvent.price)).filter(
        and_(
            ListingEvent.created_at >= start_date,
            ListingEvent.price.isnot(None)
        )
    ).scalar()
    avg_price = float(avg_price_result) if avg_price_result else 0

    # Изменение цен (сравнение с предыдущим периодом)
    prev_start = start_date - timedelta(days=days)
    prev_end = start_date

    current_avg = avg_price
    prev_avg_result = db.query(func.avg(ListingEvent.price)).filter(
        and_(
            ListingEvent.created_at >= prev_start,
            ListingEvent.created_at < prev_end,
            ListingEvent.price.isnot(None)
        )
    ).scalar()
    prev_avg = float(prev_avg_result) if prev_avg_result else 0

    price_change = ((current_avg - prev_avg) / max(prev_avg, 1)) * 100 if prev_avg > 0 else 0

    return {
        "period": {
            "days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "overview": {
            "total_games": total_games,
            "total_stores": total_stores,
            "total_agents": total_agents,
            "active_agents": active_agents,
            "events_in_period": events_in_period,
            "avg_price": round(current_avg, 2),
            "price_change": round(price_change, 2)
        }
    }


@router.get("/top-games")
async def get_top_games(
    limit: int = Query(10, ge=1, le=50, description="Лимит записей"),
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    db: Session = Depends(get_db)
):
    """Получить топ игр по количеству событий."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Топ игр по количеству событий
    top_games = db.query(
        Game.id,
        Game.title,
        func.count(ListingEvent.id).label('events_count'),
        func.avg(ListingEvent.price).label('avg_price'),
        func.min(ListingEvent.price).label('min_price'),
        func.max(ListingEvent.price).label('max_price')
    ).join(
        ListingEvent, Game.id == ListingEvent.game_id
    ).filter(
        ListingEvent.created_at >= start_date
    ).group_by(
        Game.id, Game.title
    ).order_by(
        desc('events_count')
    ).limit(limit).all()

    result = []
    for game in top_games:
        result.append({
            "id": str(game.id),
            "title": game.title,
            "events": game.events_count,
            "avgPrice": float(game.avg_price) if game.avg_price else 0,
            "minPrice": float(game.min_price) if game.min_price else 0,
            "maxPrice": float(game.max_price) if game.max_price else 0
        })

    return {"games": result}


@router.get("/store-stats")
async def get_store_statistics(
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    db: Session = Depends(get_db)
):
    """Получить статистику по магазинам."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Статистика по магазинам
    store_stats = db.query(
        Store.id,
        Store.name,
        func.count(ListingEvent.id).label('events_count'),
        func.avg(ListingEvent.price).label('avg_price')
    ).join(
        ListingEvent, Store.id == ListingEvent.store_id
    ).filter(
        ListingEvent.created_at >= start_date
    ).group_by(
        Store.id, Store.name
    ).order_by(
        desc('events_count')
    ).all()

    result = []
    for store in store_stats:
        # Расчет изменения цен для магазина
        current_avg = float(store.avg_price) if store.avg_price else 0

        # Средняя цена в предыдущем периоде
        prev_start = start_date - timedelta(days=days)
        prev_avg_result = db.query(func.avg(ListingEvent.price)).filter(
            and_(
                ListingEvent.store_id == store.id,
                ListingEvent.created_at >= prev_start,
                ListingEvent.created_at < start_date,
                ListingEvent.price.isnot(None)
            )
        ).scalar()
        prev_avg = float(prev_avg_result) if prev_avg_result else 0

        price_change = ((current_avg - prev_avg) / max(prev_avg, 1)) * 100 if prev_avg > 0 else 0

        result.append({
            "id": store.id,
            "name": store.name,
            "events": store.events_count,
            "avgPrice": current_avg,
            "priceChange": round(price_change, 2)
        })

    return {"stores": result}


@router.get("/events-by-kind")
async def get_events_by_kind(
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    db: Session = Depends(get_db)
):
    """Получить распределение событий по типам."""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Распределение по типам событий
    events_by_kind = db.query(
        ListingEvent.kind,
        func.count(ListingEvent.id).label('count')
    ).filter(
        ListingEvent.created_at >= start_date
    ).group_by(
        ListingEvent.kind
    ).all()

    total_events = sum(count for _, count in events_by_kind)

    result = []
    for kind, count in events_by_kind:
        percentage = (count / max(total_events, 1)) * 100 if total_events > 0 else 0
        result.append({
            "kind": kind.value,
            "count": count,
            "percentage": round(percentage, 1)
        })

    return {"events": result}


@router.get("/price-trends")
async def get_price_trends(
    game_id: Optional[str] = Query(None, description="ID игры"),
    store_id: Optional[str] = Query(None, description="ID магазина"),
    days: int = Query(30, ge=1, le=365, description="Период в днях"),
    db: Session = Depends(get_db)
):
    """Получить тренды цен."""
    start_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(PriceHistory).filter(
        PriceHistory.observed_at >= start_date
    )

    if game_id:
        query = query.filter(PriceHistory.game_id == game_id)
    if store_id:
        query = query.filter(PriceHistory.store_id == store_id)

    price_data = query.order_by(PriceHistory.observed_at).all()

    # Группировка по дням
    daily_data = {}
    for record in price_data:
        date_key = record.observed_at.date().isoformat()
        if date_key not in daily_data:
            daily_data[date_key] = []
        daily_data[date_key].append(float(record.price))

    # Расчет средних цен по дням
    result = []
    for date, prices in sorted(daily_data.items()):
        avg_price = sum(prices) / len(prices)
        result.append({
            "date": date,
            "avgPrice": round(avg_price, 2),
            "minPrice": min(prices),
            "maxPrice": max(prices),
            "dataPoints": len(prices)
        })

    return {"trends": result}


@router.get("/summary")
async def get_analytics_summary(
    db: Session = Depends(get_db)
):
    """Получить сводную аналитику для дашборда."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Базовая статистика
    total_games = db.query(Game).count()
    total_stores = db.query(Store).count()
    total_events = db.query(ListingEvent).count()

    # Статистика за сегодня
    today_events = db.query(ListingEvent).filter(
        ListingEvent.created_at >= today_start
    ).count()

    # Статистика за неделю
    week_events = db.query(ListingEvent).filter(
        ListingEvent.created_at >= week_start
    ).count()

    # Статистика за месяц
    month_events = db.query(ListingEvent).filter(
        ListingEvent.created_at >= month_start
    ).count()

    # Средняя цена
    avg_price_result = db.query(func.avg(ListingEvent.price)).filter(
        ListingEvent.price.isnot(None)
    ).scalar()
    avg_price = float(avg_price_result) if avg_price_result else 0

    # Топ магазинов за месяц
    top_stores = db.query(
        Store.name,
        func.count(ListingEvent.id).label('count')
    ).join(
        ListingEvent, Store.id == ListingEvent.store_id
    ).filter(
        ListingEvent.created_at >= month_start
    ).group_by(
        Store.id, Store.name
    ).order_by(
        desc('count')
    ).limit(5).all()

    # Распределение событий за месяц
    events_by_kind = db.query(
        ListingEvent.kind,
        func.count(ListingEvent.id).label('count')
    ).filter(
        ListingEvent.created_at >= month_start
    ).group_by(
        ListingEvent.kind
    ).all()

    return {
        "summary": {
            "totalGames": total_games,
            "totalStores": total_stores,
            "totalEvents": total_events,
            "avgPrice": round(avg_price, 2)
        },
        "periods": {
            "today": {"events": today_events},
            "week": {"events": week_events},
            "month": {"events": month_events}
        },
        "topStores": [
            {"name": store.name, "count": store.count}
            for store in top_stores
        ],
        "eventsByKind": [
            {"kind": kind.value, "count": count}
            for kind, count in events_by_kind
        ]
    }