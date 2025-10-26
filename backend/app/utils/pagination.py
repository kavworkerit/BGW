"""
Утилиты для пагинации в API эндпоинтах.

Следует принципу DRY - предоставляет общие компоненты для пагинации
во всех API роутерах.
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from math import ceil

T = TypeVar('T')


class PaginationParams(BaseModel):
    """Параметры пагинации для запросов."""

    skip: int = Field(0, ge=0, description="Количество записей для пропуска")
    limit: int = Field(50, ge=1, le=1000, description="Количество записей на странице")

    @validator('limit')
    def validate_limit(cls, v):
        """Валидация лимита с защитой от слишком больших значений."""
        return min(v, 1000)  # Максимальный лимит для защиты

    @property
    def offset(self) -> int:
        """Вычисление смещения для SQL запросов."""
        return self.skip

    @property
    def page_size(self) -> int:
        """Размер страницы (алиас для limit)."""
        return self.limit


class PaginatedResponse(BaseModel, Generic[T]):
    """Модель ответа с пагинацией."""

    items: List[T] = Field(description="Элементы текущей страницы")
    total: int = Field(description="Общее количество элементов")
    skip: int = Field(description="Количество пропущенных элементов")
    limit: int = Field(description="Размер страницы")
    has_next: bool = Field(description="Есть ли следующая страница")
    has_prev: bool = Field(description="Есть ли предыдущая страница")
    pages_total: int = Field(description="Общее количество страниц")
    current_page: int = Field(description="Текущая страница (1-based)")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        skip: int = 0,
        limit: int = 50
    ) -> "PaginatedResponse[T]":
        """
        Создать пагинированный ответ.

        Args:
            items: Элементы текущей страницы
            total: Общее количество элементов
            skip: Количество пропущенных элементов
            limit: Размер страницы

        Returns:
            PaginatedResponse: Ответ с мета-информацией о пагинации
        """
        pages_total = ceil(total / max(limit, 1)) if limit > 0 else 0
        current_page = (skip // limit) + 1 if limit > 0 else 1

        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_next=skip + limit < total,
            has_prev=skip > 0,
            pages_total=pages_total,
            current_page=current_page
        )


class PaginationHelper:
    """Помощник для работы с пагинацией в SQLAlchemy."""

    @staticmethod
    def apply_pagination(query, skip: int, limit: int):
        """
        Применить пагинацию к SQLAlchemy запросу.

        Args:
            query: SQLAlchemy query объект
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            Query: Запрос с примененной пагинацией
        """
        return query.offset(skip).limit(limit)

    @staticmethod
    def count_total(query) -> int:
        """
        Получить общее количество записей в запросе.

        Args:
            query: SQLAlchemy query объект

        Returns:
            int: Общее количество записей
        """
        return query.count()

    @staticmethod
    def get_paginated_results(query, skip: int = 0, limit: int = 50):
        """
        Получить пагинированные результаты из SQLAlchemy запроса.

        Args:
            query: SQLAlchemy query объект
            skip: Количество записей для пропуска
            limit: Максимальное количество записей

        Returns:
            tuple: (items, total)
        """
        total = PaginationHelper.count_total(query)
        items = PaginationHelper.apply_pagination(query, skip, limit).all()
        return items, total


def get_pagination_params(skip: int = 0, limit: int = 50) -> PaginationParams:
    """
    Dependency функция для FastAPI для извлечения параметров пагинации.

    Args:
        skip: Количество записей для пропуска (query parameter)
        limit: Максимальное количество записей (query parameter)

    Returns:
        PaginationParams: Валидированные параметры пагинации
    """
    return PaginationParams(skip=skip, limit=limit)


def create_pagination_links(
    base_url: str,
    total: int,
    skip: int,
    limit: int,
    max_links: int = 5
) -> Dict[str, Optional[str]]:
    """
    Создать ссылки для навигации по страницам (для REST API).

    Args:
        base_url: Базовый URL без параметров
        total: Общее количество элементов
        skip: Текущее смещение
        limit: Размер страницы
        max_links: Максимальное количество ссылок на страницы

    Returns:
        Dict[str, Optional[str]]: Словарь с ссылками навигации
    """
    pages_total = ceil(total / max(limit, 1)) if limit > 0 else 0
    current_page = (skip // limit) + 1 if limit > 0 else 1

    links = {
        "first": f"{base_url}?skip=0&limit={limit}" if total > 0 else None,
        "last": f"{base_url}?skip={(pages_total - 1) * limit}&limit={limit}" if pages_total > 0 else None,
        "prev": f"{base_url}?skip=max(0, {skip - limit})&limit={limit}" if skip > 0 else None,
        "next": f"{base_url}?skip={skip + limit}&limit={limit}" if skip + limit < total else None,
    }

    return links