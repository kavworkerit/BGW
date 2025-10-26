"""
Сервис дедупликации событий с использованием signature_hash.

Реализует вычисление хешей для предотвращения дублирования событий
на основе нормализованных данных.
"""

import hashlib
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.listing_event import ListingEvent


def normalize_text(text: str) -> str:
    """
    Нормализация текста для сравнения.

    Args:
        text: Исходный текст

    Returns:
        Нормализованный текст
    """
    if not text:
        return ""

    # Приводим к нижнему регистру
    text = text.lower().strip()

    # Удаляем лишние пробелы
    text = re.sub(r'\s+', ' ', text)

    # Удаляем мусорные слова для настольных игр
    junk_words = [
        'настольная игра', 'настольные игры', 'издание', 'делюкс', 'эксклюзив',
        'набор', 'база', 'дополнение', 'расширение', 'версия', 'редакция'
    ]

    for word in junk_words:
        text = text.replace(word, '')

    # Удаляем спецсимвуры, кроме пробелов и дефисов
    text = re.sub(r'[^\w\s\-]', '', text)

    # Удаляем множественные пробелы снова
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def calculate_signature_hash(event_data: Dict[str, Any]) -> str:
    """
    Вычисление signature_hash для дедупликации событий.

    Args:
        event_data: Данные события

    Returns:
        SHA256 хеш
    """
    # Нормализуем заголовок
    title = normalize_text(event_data.get('title', ''))

    # Получаем store_id
    store_id = event_data.get('store_id', '')

    # Нормализуем издание
    edition = normalize_text(event_data.get('edition', ''))

    # Округляем цену до целого или null
    price = event_data.get('price')
    if price is not None:
        try:
            round_price = str(int(round(float(price))))
        except (ValueError, TypeError):
            round_price = 'null'
    else:
        round_price = 'null'

    # Создаем бакет по дате (24 часа)
    now = datetime.now(timezone.utc)
    date_bucket = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Формируем базовую строку для хеширования
    base = f"{title}|{store_id}|{edition}|{round_price}|{date_bucket.isoformat()}"

    # Вычисляем SHA256
    signature_hash = hashlib.sha256(base.encode('utf-8')).hexdigest()

    return signature_hash


def is_duplicate_event(
    db: Session,
    signature_hash: str,
    hours_back: int = 72
) -> Optional[ListingEvent]:
    """
    Проверка на дубликат события.

    Args:
        db: Сессия базы данных
        signature_hash: Хеш для проверки
        hours_back: Период проверки в часах

    Returns:
        Найденный дубликат или None
    """
    since = datetime.now(timezone.utc).replace(tzinfo=None) - \
             datetime.timedelta(hours=hours_back)

    duplicate = db.query(ListingEvent).filter(
        and_(
            ListingEvent.signature_hash == signature_hash,
            ListingEvent.created_at >= since
        )
    ).first()

    return duplicate


def create_event_with_deduplication(
    db: Session,
    event_data: Dict[str, Any]
) -> tuple[ListingEvent, bool]:
    """
    Создание события с проверкой на дубликаты.

    Args:
        db: Сессия базы данных
        event_data: Данные для создания события

    Returns:
        (Событие, флаг дубликата)
    """
    # Вычисляем signature_hash
    signature_hash = calculate_signature_hash(event_data)

    # Проверяем на дубликат
    duplicate = is_duplicate_event(db, signature_hash)
    if duplicate:
        return duplicate, True

    # Создаем новое событие
    event_data['signature_hash'] = signature_hash
    event = ListingEvent(**event_data)

    db.add(event)
    db.commit()
    db.refresh(event)

    return event, False


def cleanup_old_duplicates(db: Session, days_old: int = 7) -> int:
    """
    Очистка старых дубликатов.

    Args:
        db: Сессия базы данных
        days_old: Возраст в днях для удаления

    Returns:
        Количество удаленных записей
    """
    cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - \
                  datetime.timedelta(days=days_old)

    # Ищем дубликаты старше указанной даты
    duplicates = db.query(ListingEvent).filter(
        ListingEvent.created_at < cutoff_date
    ).all()

    count = len(duplicates)

    for duplicate in duplicates:
        db.delete(duplicate)

    db.commit()

    return count