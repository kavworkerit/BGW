# Настройка мониторинга BGW с Prometheus и Grafana

## Обзор

Система мониторинга включает:
- **Prometheus** - сбор метрик с приложения
- **Grafana** - визуализация метрик и алертов
- **Node Exporter** - системные метрики (опционально)
- **Custom Alerts** - алерты по бизнес-метрикам

## Запуск мониторинга

### 1. Через Docker Compose

```bash
# Запуск всех сервисов включая мониторинг
docker-compose up -d

# Запуск только мониторинга (если уже запущены основные сервисы)
docker-compose up -d prometheus grafana
```

### 2. Порты доступа

После запуска сервисы будут доступны:

- **Grafana**: http://localhost:3001
  - Логин: admin
  - Пароль: admin
- **Prometheus**: http://localhost:9090
  - Цели: http://localhost:9090/targets
- **API**: http://localhost:8000
  - Метрики: http://localhost:8000/api/metrics/prometheus
  - Здоровье: http://localhost:8000/api/metrics/health

## Метрики BGW

### Агенты
- `active_agents` - количество активных агентов
- `agent_runs_total` - общее количество запусков (с метками agent_id, status)
- `agent_pages_fetched_total` - общее количество загруженных страниц
- `agent_duration_seconds` - время выполнения агента
- `daily_pages_used` - использовано страниц за сегодня
- `daily_pages_cap` - лимит страниц за день

### События
- `events_created_total` - созданные события (с метками event_type, store_id)

### Уведомления
- `notifications_sent_total` - отправленные уведомления (с метками channel, status)
- `notifications_delivered_total` - доставленные уведомления
- `rules_active` - количество активных правил

### API
- `api_requests_total` - запросы к API (с метками method, endpoint, status)
- `api_response_time_seconds` - время ответа API (гистограмма)

### Система
- `system_health` - здоровье системы (1=здоров, 0=проблемы)
- `database_connections_active` - активные подключения к БД
- `redis_connections_active` - активные подключения к Redis

## Grafana Дашборды

### Основной дашборд
- **URL**: http://localhost:3001/d/bgw-overview
- **Содержит**: обзор системы, активных агентов, производительность
- **Обновление**: каждые 30 секунд

### Создание кастомных дашбордов

1. Создать JSON файл в формате Grafana
2. Импортировать через UI Grafana
3. Использовать переменные из Prometheus метрик

Пример запроса в Grafana:
```
rate(agent_pages_fetched_total[5m])
sum(rate(events_created_total[5m]))
histogram_quantile(0.95, api_response_time_seconds)
```

## Алерты

### Настройка алертов

Алерты определены в `deploy/bgw_rules.yml`:

#### Критичные (Critical)
- **API unavailable** - API недоступен > 1 минуты
- **Database issues** - проблемы с подключением к БД
- **No agent runs** - нет запусков агентов > 10 минут

#### Предупреждения (Warning)
- **High error rate** - высокое количество ошибок API
- **High latency** - медленные ответы API > 2с
- **Notification failures** - много недоставленных уведомлений
- **Daily quota exceeded** - превышение дневного лимита

### Получение алертов

- **Email**: нужно настроить SMTP в Grafana
- **Slack**: webhook интеграция
- **Telegram**: бот интеграция

## Добавление Node Exporter (опционально)

Для системных метрик добавить в docker-compose.yml:

```yaml
node-exporter:
  image: prom/node-exporter:latest
  ports:
    - "9100:9100"
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/rootfs:ro
  restart: unless-stopped
```

И добавить в Prometheus конфигурацию:

```yaml
- job_name: 'node-exporter'
  static_configs:
    - targets: ['node-exporter:9100']
  scrape_interval: 30s
```

## Расширенные метрики

### Бизнес-метрики
Добавить в `app/metrics.py`:

```python
# Метрики эффективности скрейпинга
SCRAPING_SUCCESS_RATE = Gauge(
    'scraping_success_rate',
    'Успешность скрапинга (%)',
    registry=REGISTRY
)

# Метрики качества данных
DATA_QUALITY_SCORE = Gauge(
    'data_quality_score',
    'Оценка качества данных',
    registry=REGISTRY
)

# Метрики покрытия
STORE_COVERAGE = Gauge(
    'store_coverage',
    'Покрытие магазинов',
    registry=REGISTRY
)
```

### Мониторинг внешних сервисов

```python
# В health_metrics.py
async def check_external_services():
    health_status = 1

    # Проверяем Ollama
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_URL}/api/tags", timeout=5) as resp:
                if resp.status != 200:
                    health_status = 0
    except:
        health_status = 0

    SYSTEM_HEALTH.set(health_status)
```

## Траблшутинг

### Профилирование
```python
# Добавить в API middleware
import cProfile
import pstats

@app.middleware("http")
async def profile_middleware(request, call_next):
    if PROFILING_ENABLED:
        pr = cProfile.Profile()
        pr.enable()

    response = await call_next(request)

    if PROFILING_ENABLED:
        pr.disable()
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        # Сохранить профиль или отправить в сервис
```

### Логирование производительности
```python
import structlog

logger = structlog.get_logger()

@time_agent_run()
async def run_agent_with_logging(agent_id: str):
    logger.info("Agent started", agent_id=agent_id)
    start_time = time.time()

    try:
        result = await run_agent(agent_id)
        duration = time.time() - start_time
        logger.info(
            "Agent completed",
            agent_id=agent_id,
            duration=duration,
            events_count=len(result)
        )
        return result
    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Agent failed",
            agent_id=agent_id,
            duration=duration,
            error=str(e)
        )
        raise
```

## Резервирование и восстановление

### Конфигурация Prometheus
```yaml
storage:
  tsdb:
    retention.time: 30d
    retention.size: 10GB
```

### Настройка алертменеджера
```yaml
alertmanager:
  image: prom/alertmanager:latest
  ports:
    - "9093:9093"
  volumes:
    - ./deploy/alertmanager.yml:/etc/alertmanager/alertmanager.yml
```

## API для метрик

### Основные эндпоинты
- `GET /api/metrics/prometheus` - метрики в формате Prometheus
- `GET /api/metrics/health` - здоровье системы в JSON
- `GET /api/metrics/stats` - детальная статистика
- `GET /api/metrics/targets` - цели для мониторинга
- `GET /api/metrics/reset` - сброс метрик (только для разработки)

### Использование метрик в коде

```python
from app.metrics import MetricsCollector

# Запуск агента с метриками
@MetricsCollector.time_agent_run(lambda: agent_id: agent["id"])
async def run_agent_with_metrics(agent):
    MetricsCollector.record_agent_run(agent["id"], "started")

    try:
        start_time = time.time()
        result = await run_agent_logic(agent)
        duration = time.time() - start_time

        MetricsCollector.record_agent_run(agent["id"], "success")
        MetricsCollector.record_agent_duration(agent["id"], duration)

        return result
    except Exception as e:
        MetricsCollector.record_agent_run(agent["id"], "error")
        raise
```

## Production советы

### 1. Безопасность
- Ограничить доступ к Grafana (IP whitelist)
- Использовать HTTPS для Prometheus
- Настроить аутентификацию для API метрик

### 2. Оптимизация
- Настроить интервал сбора метрик (15-60 секунд)
- Использовать гистограммы для времени выполнения
- Ограничить количество метрик (отключать ненужное)

### 3. Хранение
- Использовать tsdb retention в Prometheus
- Регулярная очистка старых метрик
- Мониторинг дискового пространства

### 4. Мониторинг
- Настроить алерты на critical метрики
- Проверять работу графаны и прометея
- Использовать health checks для всех сервисов

## Ссылки

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Node Exporter](https://github.com/prometheus/node_exporter)
- [BGW Metrics Dashboard](http://localhost:3001/d/bgw-overview)

---

**Готовность к производству**: ✅
**Сложность**: Средняя
**Время настройки**: 30-60 минут