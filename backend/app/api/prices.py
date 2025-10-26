from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import csv
import io

from app.core.database import get_db
from app.models.price_history import PriceHistory
from app.models.game import Game
from app.models.store import Store

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_price_history(
    game_id: Optional[str] = Query(None),
    store_ids: Optional[List[str]] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    days: Optional[int] = Query(None, ge=1, le=730),  # до 2 лет
    db: Session = Depends(get_db)
):
    """Получить историю цен с фильтрацией."""
    query = db.query(
        PriceHistory,
        Game.title.label('game_title'),
        Store.name.label('store_name')
    ).join(
        Game, PriceHistory.game_id == Game.id
    ).join(
        Store, PriceHistory.store_id == Store.id
    )

    # Фильтр по игре
    if game_id:
        query = query.filter(PriceHistory.game_id == game_id)

    # Фильтр по магазинам
    if store_ids:
        query = query.filter(PriceHistory.store_id.in_(store_ids))

    # Фильтр по дате
    if from_date:
        try:
            from_dt = datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(PriceHistory.observed_at >= from_dt)
        except ValueError:
            raise HTTPException(400, "Неверный формат даты from_date. Используйте YYYY-MM-DD")

    if to_date:
        try:
            to_dt = datetime.strptime(to_date, '%Y-%m-%d')
            query = query.filter(PriceHistory.observed_at <= to_dt)
        except ValueError:
            raise HTTPException(400, "Неверный формат даты to_date. Используйте YYYY-MM-DD")

    # Фильтр по количеству дней (если не указаны даты)
    if days and not from_date and not to_date:
        from_dt = datetime.now() - timedelta(days=days)
        query = query.filter(PriceHistory.observed_at >= from_dt)

    # Сортировка по дате
    query = query.order_by(desc(PriceHistory.observed_at))

    # Ограничение количества записей (для производительности)
    results = query.limit(10000).all()

    # Форматирование результата
    price_data = []
    for price_hist, game_title, store_name in results:
        price_data.append({
            'game_id': price_hist.game_id,
            'game_title': game_title,
            'store_id': price_hist.store_id,
            'store_name': store_name,
            'observed_at': price_hist.observed_at.isoformat(),
            'price': float(price_hist.price),
            'currency': price_hist.currency
        })

    return price_data


@router.get("/export/csv")
async def export_price_history_csv(
    game_id: Optional[str] = Query(None),
    store_ids: Optional[List[str]] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    days: Optional[int] = Query(None, ge=1, le=730),
    format: str = Query("csv", regex="^(csv)$"),
    db: Session = Depends(get_db)
):
    """Экспорт истории цен в CSV."""
    # Получаем данные (используем ту же логику)
    query = db.query(
        PriceHistory,
        Game.title.label('game_title'),
        Store.name.label('store_name')
    ).join(
        Game, PriceHistory.game_id == Game.id
    ).join(
        Store, PriceHistory.store_id == Store.id
    )

    # Применяем те же фильтры
    if game_id:
        query = query.filter(PriceHistory.game_id == game_id)

    if store_ids:
        query = query.filter(PriceHistory.store_id.in_(store_ids))

    if from_date:
        try:
            from_dt = datetime.strptime(from_date, '%Y-%m-%d')
            query = query.filter(PriceHistory.observed_at >= from_dt)
        except ValueError:
            raise HTTPException(400, "Неверный формат даты")

    if to_date:
        try:
            to_dt = datetime.strptime(to_date, '%Y-%m-%d')
            query = query.filter(PriceHistory.observed_at <= to_dt)
        except ValueError:
            raise HTTPException(400, "Неверный формат даты")

    if days and not from_date and not to_date:
        from_dt = datetime.now() - timedelta(days=days)
        query = query.filter(PriceHistory.observed_at >= from_dt)

    query = query.order_by(desc(PriceHistory.observed_at))
    results = query.all()

    # Создаем CSV
    output = io.StringIO()
    writer = csv.writer(output)

    # Заголовки
    writer.writerow([
        'Game Title',
        'Store Name',
        'Price',
        'Currency',
        'Observed At'
    ])

    # Данные
    for price_hist, game_title, store_name in results:
        writer.writerow([
            game_title,
            store_name,
            float(price_hist.price),
            price_hist.currency,
            price_hist.observed_at.isoformat()
        ])

    # Создаем ответ
    output.seek(0)

    # Имя файла
    filename = f"price_history"
    if game_id:
        filename += f"_game_{game_id}"
    if from_date:
        filename += f"_from_{from_date}"
    if to_date:
        filename += f"_to_{to_date}"
    filename += f"_{datetime.now().strftime('%Y%m%d')}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/stats", response_model=Dict[str, Any])
async def get_price_stats(
    game_id: str = Query(...),
    store_ids: Optional[List[str]] = Query(None),
    days: int = Query(30, ge=1, le=730),
    db: Session = Depends(get_db)
):
    """Получить статистику по ценам для игры."""
    from_dt = datetime.now() - timedelta(days=days)

    query = db.query(PriceHistory).filter(
        and_(
            PriceHistory.game_id == game_id,
            PriceHistory.observed_at >= from_dt
        )
    )

    if store_ids:
        query = query.filter(PriceHistory.store_id.in_(store_ids))

    results = query.all()

    if not results:
        return {
            'game_id': game_id,
            'period_days': days,
            'data_points': 0,
            'min_price': None,
            'max_price': None,
            'avg_price': None,
            'stores': []
        }

    prices = [float(r.price) for r in results]
    store_prices = {}

    for result in results:
        store_id = result.store_id
        if store_id not in store_prices:
            store_prices[store_id] = []
        store_prices[store_id].append(float(result.price))

    # Статистика по магазинам
    stores_stats = []
    for store_id, store_price_list in store_prices.items():
        store = db.query(Store).filter(Store.id == store_id).first()
        stores_stats.append({
            'store_id': store_id,
            'store_name': store.name if store else store_id,
            'min_price': min(store_price_list),
            'max_price': max(store_price_list),
            'avg_price': sum(store_price_list) / len(store_price_list),
            'data_points': len(store_price_list)
        })

    return {
        'game_id': game_id,
        'period_days': days,
        'data_points': len(results),
        'min_price': min(prices),
        'max_price': max(prices),
        'avg_price': sum(prices) / len(prices),
        'stores': stores_stats
    }