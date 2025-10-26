"""
Модуль для сбора Prometheus метрик приложения.

Собирает метрики по:
- Производительности агентов
- Успешности операций
- Количеству обработанных данных
- Состоянию системы
"""

import time
import functools
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Custom registry для изоляции метрик приложения
REGISTRY = CollectorRegistry()

# Счетчики событий
AGENT_RUNS_TOTAL = Counter(
    'agent_runs_total',
    'Общее количество запусков агентов',
    ['agent_id', 'status'],
    registry=REGISTRY
)

AGENT_PAGES_FETCHED_TOTAL = Counter(
    'agent_pages_fetched_total',
    'Общее количество загруженных страниц агентами',
    ['agent_id'],
    registry=REGISTRY
)

EVENTS_CREATED_TOTAL = Counter(
    'events_created_total',
    'Общее количество созданных событий',
    ['event_type', 'store_id'],
    registry=REGISTRY
)

NOTIFICATIONS_SENT_TOTAL = Counter(
    'notifications_sent_total',
    'Общее количество отправленных уведомлений',
    ['channel', 'status'],
    registry=REGISTRY
)

NOTIFICATIONS_DELIVERED_TOTAL = Counter(
    'notifications_delivered_total',
    'Общее количество доставленных уведомлений',
    ['channel'],
    registry=REGISTRY
)

API_REQUESTS_TOTAL = Counter(
    'api_requests_total',
    'Общее количество API запросов',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

# Гистограммы времени выполнения
AGENT_DURATION_SECONDS = Histogram(
    'agent_duration_seconds',
    'Время выполнения агента в секундах',
    ['agent_id'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 300.0],
    registry=REGISTRY
)

API_RESPONSE_TIME_SECONDS = Histogram(
    'api_response_time_seconds',
    'Время ответа API в секундах',
    ['method', 'endpoint'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=REGISTRY
)

DATABASE_QUERY_DURATION_SECONDS = Histogram(
    'database_query_duration_seconds',
    'Время выполнения запроса к БД в секундах',
    ['query_type'],
    buckets=[0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0],
    registry=REGISTRY
)

# Измеряемые значения (gauges)
ACTIVE_AGENTS = Gauge(
    'active_agents',
    'Количество активных агентов',
    registry=REGISTRY
)

DAILY_PAGES_USED = Gauge(
    'daily_pages_used',
    'Количество использованных страниц за сегодня',
    registry=REGISTRY
)

DAILY_PAGES_CAP = Gauge(
    'daily_pages_cap',
    'Лимит страниц за день',
    registry=REGISTRY
)

RULES_ACTIVE = Gauge(
    'rules_active',
    'Количество активных правил уведомлений',
    registry=REGISTRY
)

SYSTEM_HEALTH = Gauge(
    'system_health',
    'Состояние здоровья системы (1=здоров, 0=проблемы)',
    registry=REGISTRY
)

DATABASE_CONNECTIONS_ACTIVE = Gauge(
    'database_connections_active',
    'Количество активных подключений к БД',
    registry=REGISTRY
)

REDIS_CONNECTIONS_ACTIVE = Gauge(
    'redis_connections_active',
    'Количество активных подключений к Redis',
    registry=REGISTRY
)

# Кастомные метрики
class MetricsCollector:
    """Класс для сбора кастомных метрик."""

    @staticmethod
    def record_agent_run(agent_id: str, status: str):
        """Запустить запуск агента."""
        AGENT_RUNS_TOTAL.labels(agent_id=agent_id, status=status).inc()

    @staticmethod
    def record_page_fetched(agent_id: str):
        """Записать загрузку страницы."""
        AGENT_PAGES_FETCHED_TOTAL.labels(agent_id=agent_id).inc()

    @staticmethod
    def record_event_created(event_type: str, store_id: str):
        """Записать создание события."""
        EVENTS_CREATED_TOTAL.labels(event_type=event_type, store_id=store_id).inc()

    @staticmethod
    def record_notification_sent(channel: str, status: str):
        """Записать отправку уведомления."""
        NOTIFICATIONS_SENT_TOTAL.labels(channel=channel, status=status).inc()

    @staticmethod
    def record_notification_delivered(channel: str):
        """Записать доставку уведомления."""
        NOTIFICATIONS_DELIVERED_TOTAL.labels(channel=channel).inc()

    @staticmethod
    def record_api_request(method: str, endpoint: str, status: str):
        """Записать API запрос."""
        API_REQUESTS_TOTAL.labels(method=method, endpoint=endpoint, status=status).inc()

    @staticmethod
    def record_agent_duration(agent_id: str, duration: float):
        """Записать время выполнения агента."""
        AGENT_DURATION_SECONDS.labels(agent_id=agent_id).observe(duration)

    @staticmethod
    def record_api_response_time(method: str, endpoint: str, duration: float):
        """Записать время ответа API."""
        API_RESPONSE_TIME_SECONDS.labels(method=method, endpoint=endpoint).observe(duration)

    @staticmethod
    def record_database_query(query_type: str, duration: float):
        """Записать время запроса к БД."""
        DATABASE_QUERY_DURATION_SECONDS.labels(query_type=query_type).observe(duration)

    @staticmethod
    def update_active_agents(count: int):
        """Обновить количество активных агентов."""
        ACTIVE_AGENTS.set(count)

    @staticmethod
    def update_daily_pages_used(count: int):
        """Обновить количество использованных страниц."""
        DAILY_PAGES_USED.set(count)

    @staticmethod
    def update_daily_pages_cap(count: int):
        """Обновить лимит страниц за день."""
        DAILY_PAGES_CAP.set(count)

    @staticmethod
    def update_active_rules(count: int):
        """Обновить количество активных правил."""
        RULES_ACTIVE.set(count)

    @staticmethod
    def update_system_health(healthy: bool):
        """Обновить состояние системы."""
        SYSTEM_HEALTH.set(1 if healthy else 0)

    @staticmethod
    def update_database_connections(count: int):
        """Обновить количество подключений к БД."""
        DATABASE_CONNECTIONS_ACTIVE.set(count)

    @staticmethod
    def update_redis_connections(count: int):
        """Обновить количество подключений к Redis."""
        REDIS_CONNECTIONS_ACTIVE.set(count)


def timing_decorator(histogram, labels_func=None):
    """Декоратор для измерения времени выполнения функции."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                if labels_func:
                    labels = labels_func(*args, **kwargs)
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)

                return result
            except Exception as e:
                duration = time.time() - start_time
                if labels_func:
                    labels = labels_func(*args, **kwargs)
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)
                raise e
        return wrapper
    return decorator


def async_timing_decorator(histogram, labels_func=None):
    """Асинхронный декоратор для измерения времени выполнения."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time

                if labels_func:
                    labels = labels_func(*args, **kwargs)
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)

                return result
            except Exception as e:
                duration = time.time() - start_time
                if labels_func:
                    labels = labels_func(*args, **kwargs)
                    histogram.labels(**labels).observe(duration)
                else:
                    histogram.observe(duration)
                raise e
        return wrapper
    return decorator


# Кастомные декораторы для часто используемых метрик
def time_agent_run(agent_id_label_func=None):
    """Декоратор для времени выполнения агента."""
    def labels_func(*args, **kwargs):
        if agent_id_label_func:
            return {'agent_id': agent_id_label_func(*args, **kwargs)}
        return {'agent_id': 'unknown'}

    return async_timing_decorator(AGENT_DURATION_SECONDS, labels_func)


def time_api_request():
    """Декоратор для времени ответа API."""
    def labels_func(*args, **kwargs):
        # Определяем метод и endpoint из аргументов функции
        method = 'unknown'
        endpoint = 'unknown'

        if args and hasattr(args[0], '__self__'):
            # Это метод класса
            if hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__.lower()
                if 'router' in class_name:
                    # FastAPI route handler
                    request = kwargs.get('request') or (args[1] if len(args) > 1 else None)
                    if request:
                        method = request.method.lower()
                        endpoint = request.url.path or 'unknown'

        return {'method': method, 'endpoint': endpoint}

    return timing_decorator(API_RESPONSE_TIME_SECONDS, labels_func)


def time_database_query(query_type_label_func=None):
    """Декоратор для времени запроса к БД."""
    def labels_func(*args, **kwargs):
        if query_type_label_func:
            return {'query_type': query_type_label_func(*args, **kwargs)}
        return {'query_type': 'unknown'}

    return timing_decorator(DATABASE_QUERY_DURATION_SECONDS, labels_func)


class PrometheusMiddleware:
    """Middleware для FastAPI для сбора метрик API запросов."""

    def __init__(self, app):
        self.app = app
        self.app.middleware("http")(self.collect_metrics)

    async def collect_metrics(self, request, call_next):
        """Собрать метрики для запроса."""
        start_time = time.time()

        response = await call_next(request)

        duration = time.time() - start_time

        # Записываем метрики запроса
        MetricsCollector.record_api_request(
            method=request.method,
            endpoint=request.url.path or 'unknown',
            status=str(response.status_code)
        )

        MetricsCollector.record_api_response_time(
            method=request.method,
            endpoint=request.url.path or 'unknown',
            duration=duration
        )

        return response


def get_metrics_registry() -> CollectorRegistry:
    """Получить реестр метрик."""
    return REGISTRY


def generate_metrics() -> str:
    """Сгенерировать текстовый формат метрик."""
    try:
        return generate_latest(REGISTRY)
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return "# Error generating metrics\n"


def get_health_metrics() -> Dict[str, Any]:
    """Получить метрики здоровья системы."""
    try:
        # Здесь можно добавить проверку зависимостей
        health_status = 1  # Предполагаем, что система здорова

        # Проверяем критичные компоненты
        # TODO: Добавить реальные проверки БД, Redis, etc.

        return {
            'system_health': health_status,
            'active_agents': ACTIVE_AGENTS._value._value,
            'daily_pages_used': DAILY_PAGES_USED._value._value,
            'daily_pages_cap': DAILY_PAGES_CAP._value._value,
            'database_connections': DATABASE_CONNECTIONS_ACTIVE._value._value,
            'redis_connections': REDIS_CONNECTIONS_ACTIVE._value._value
        }
    except Exception as e:
        logger.error(f"Error getting health metrics: {e}")
        return {
            'system_health': 0,
            'error': str(e)
        }