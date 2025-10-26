"""
API эндпоинты для экспорта Prometheus метрик.

Предоставляют:
- /metrics - текстовый формат Prometheus
- /health - метрики здоровья системы
- /metrics/health - объединенный эндпоинт
"""

from fastapi import APIRouter, Response, Request, HTTPException
from fastapi.responses import PlainTextResponse, JSONResponse
from typing import Dict, Any
import logging
import time

from app.metrics import (
    generate_metrics,
    get_health_metrics,
    get_metrics_registry
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/metrics", tags=["metrics"])


@router.get("/prometheus", response_model=str)
async def get_prometheus_metrics():
    """
    Экспорт метрик в формате Prometheus.

    Эндпоинт: GET /api/metrics/prometheus
    """
    try:
        metrics_text = generate_metrics()
        return PlainTextResponse(
            content=metrics_text,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
    except Exception as e:
        logger.error(f"Error generating Prometheus metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate metrics"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_health_metrics_json():
    """
    Метрики здоровья системы в JSON формате.

    Эндпоинт: GET /api/metrics/health
    """
    try:
        health_data = get_health_metrics()
        status_code = 200 if health_data.get('system_health', 0) == 1 else 503

        return JSONResponse(
            content=health_data,
            status_code=status_code
        )
    except Exception as e:
        logger.error(f"Error getting health metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get health metrics"
        )


@router.get("/", response_model=Dict[str, Any])
async def get_metrics_overview():
    """
    Общая информация о метриках.

    Эндпоинт: GET /api/metrics/
    """
    try:
        health_data = get_health_metrics()
        registry = get_metrics_registry()

        # Собираем базовую статистику
        metrics_summary = {
            "health": health_data,
            "metrics_count": len(registry._collector_to_names),
            "status": "healthy" if health_data.get('system_health', 0) == 1 else "unhealthy"
        }

        return JSONResponse(content=metrics_summary)
    except Exception as e:
        logger.error(f"Error getting metrics overview: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get metrics overview"
        )


@router.get("/stats", response_model=Dict[str, Any])
async def get_detailed_stats():
    """
    Детальная статистика системы.

    Эндпоинт: GET /api/metrics/stats
    """
    try:
        health_data = get_health_metrics()

        # Расширенная статистика
        detailed_stats = {
            "system": {
                "health": health_data.get('system_health', 0),
                "status": "healthy" if health_data.get('system_health', 0) == 1 else "unhealthy"
            },
            "agents": {
                "active": health_data.get('active_agents', 0),
                "pages_used_today": health_data.get('daily_pages_used', 0),
                "pages_daily_cap": health_data.get('daily_pages_cap', 0),
                "usage_percentage": 0
            },
            "database": {
                "active_connections": health_data.get('database_connections', 0)
            },
            "cache": {
                "active_connections": health_data.get('redis_connections', 0)
            },
            "notifications": {
                "active_rules": health_data.get('rules_active', 0)
            }
        }

        # Вычисляем процент использования
        pages_cap = health_data.get('daily_pages_cap', 1)
        if pages_cap > 0:
            pages_used = health_data.get('daily_pages_used', 0)
            detailed_stats["agents"]["usage_percentage"] = round(
                (pages_used / pages_cap) * 100, 2
            )

        return JSONResponse(content=detailed_stats)
    except Exception as e:
        logger.error(f"Error getting detailed stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get detailed stats"
        )


# Алиас для стандартного эндпоинта Prometheus
@router.get("/prometheus", response_model=str, include_in_schema=False)
async def metrics_alias():
    """Алиас для /metrics compatibility."""
    return await get_prometheus_metrics()


class PrometheusMetricsMiddleware:
    """Middleware для автоматического сбора метрик запросов."""

    def __init__(self):
        pass

    async def __call__(self, request: Request, call_next):
        """Обработать запрос и собрать метрики."""
        from app.metrics import MetricsCollector, API_RESPONSE_TIME_SECONDS

        start_time = time.time()

        try:
            response = await call_next(request)

            # Собираем метрики только если нет ошибок
            if response.status_code < 400:
                duration = time.time() - start_time
                MetricsCollector.record_api_response_time(
                    method=request.method,
                    endpoint=request.url.path or "unknown",
                    duration=duration
                )

                MetricsCollector.record_api_request(
                    method=request.method,
                    endpoint=request.url.path or "unknown",
                    status=str(response.status_code)
                )

            return response

        except Exception as e:
            # Записываем метрику ошибки
            MetricsCollector.record_api_request(
                method=request.method,
                endpoint=request.url.path or "unknown",
                status="500"
            )
            raise e


# Дополнительные служебные эндпоинты
@router.post("/reset")
async def reset_metrics():
    """
    Сбросить все метрики (только для разработки/тестов).

    Эндпоинт: POST /api/metrics/reset
    """
    try:
        from app.metrics import REGISTRY

        # Очищаем все метрики
        for collector in REGISTRY._collector_to_names.keys():
            REGISTRY.unregister(collector)

        logger.info("Metrics reset")
        return JSONResponse(
            content={"message": "Metrics reset successfully"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to reset metrics"
        )


@router.get("/targets")
async def get_targets():
    """
    Список целей для мониторинга (Prometheus targets).

    Эндпоинт: GET /api/metrics/targets
    """
    try:
        targets = [
            {
                "targets": [
                    f"{request.url.netloc}:8000"
                ],
                "labels": {
                    "job": "bgw-api",
                    "instance": request.url.netloc
                }
            }
        ]

        return JSONResponse(content=targets)
    except Exception as e:
        logger.error(f"Error getting targets: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get targets"
        )


# Эндпоинт для health checks (если нужен отдельный от других)
@router.get("/health/live")
async def liveness_probe():
    """
    Liveness probe для Kubernetes.

    Эндпоинт: GET /api/metrics/health/live
    """
    return JSONResponse(
        content={"status": "healthy"},
        status_code=200
    )


@router.get("/health/ready")
async def readiness_probe():
    """
    Readiness probe для Kubernetes.

    Эндпоинт: GET /api/metrics/health/ready
    """
    try:
        health_data = get_health_metrics()

        # Проверяем, что система готова к работе
        if health_data.get('system_health', 0) == 1:
            return JSONResponse(
                content={"status": "ready"},
                status_code=200
            )
        else:
            return JSONResponse(
                content={"status": "not_ready"},
                status_code=503
            )
    except Exception as e:
        logger.error(f"Error in readiness probe: {e}")
        return JSONResponse(
            content={"status": "not_ready"},
            status_code=503
        )