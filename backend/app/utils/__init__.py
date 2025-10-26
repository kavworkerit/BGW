"""
Утилиты BGW проекта.

Содержит общие компоненты для повторного использования в разных частях приложения.
"""

from .pagination import (
    PaginationParams,
    PaginatedResponse,
    PaginationHelper,
    get_pagination_params,
    create_pagination_links
)

__all__ = [
    'PaginationParams',
    'PaginatedResponse',
    'PaginationHelper',
    'get_pagination_params',
    'create_pagination_links'
]