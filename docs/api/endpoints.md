# API Эндпоинты

## Общая информация

- **Base URL**: `http://localhost:8000`
- **API Documentation**: `/docs` (Swagger UI)
- **Authentication**: JWT токены (локальная однопользовательская)
- **Content-Type**: `application/json`

## Аутентификация

### POST /auth/login
Локальный вход пользователя.

```json
// Request
{
  "username": "admin",
  "password": "password"
}

// Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Игры (Watchlist)

### GET /games
Получить список игр с пагинацией и фильтрами.

**Query Parameters:**
- `skip`: int (default: 0) - Количество записей для пропуска
- `limit`: int (default: 50, max: 1000) - Количество записей на странице
- `search`: string (поиск по названию или синонимам)
- `publisher`: string (фильтр по издателю)
- `min_players`: int (минимальное количество игроков)
- `max_players`: int (максимальное количество игроков)
- `min_playtime`: int (минимальное время игры в минутах)
- `max_playtime`: int (максимальное время игры в минутах)
- `tags`: string (теги через запятую)
- `language`: string (язык игры: RU, EN)

```json
// Response
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Громкое дело",
      "synonyms": ["Gromkoe Delo"],
      "bgg_id": "391819",
      "publisher": "Hobby Games",
      "tags": ["детектив", "расследование"],
      "description": "Детективная игра...",
      "min_players": 1,
      "max_players": 4,
      "min_playtime": 45,
      "max_playtime": 150,
      "year_published": 2023,
      "language": "RU",
      "complexity": 2.5,
      "image_url": "https://example.com/image.jpg",
      "rating_bgg": 7.8,
      "rating_users": 8.1,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50,
  "has_next": false,
  "has_prev": false,
  "pages_total": 1,
  "current_page": 1
}
```

### POST /games
Добавить новую игру в watchlist.

```json
// Request
{
  "title": "Громкое дело",
  "synonyms": ["Gromkoe Delo"],
  "bgg_id": "391819",
  "publisher": "Hobby Games",
  "tags": ["детектив", "расследование"],
  "description": "Детективная игра...",
  "min_players": 1,
  "max_players": 4,
  "min_playtime": 45,
  "max_playtime": 150,
  "year_published": 2023,
  "language": "RU",
  "complexity": 2.5,
  "image_url": "https://example.com/image.jpg"
}
```

### PUT /games/{id}
Обновить информацию об игре.

### DELETE /games/{id}
Удалить игру из watchlist.

### GET /games/{id}/events
Получить события для конкретной игры.

**Query Parameters:**
- `skip`: int (default: 0) - Количество записей для пропуска
- `limit`: int (default: 50, max: 1000) - Количество записей на странице
- `store_id`: string - Фильтр по магазину
- `kind`: string (announce|preorder|release|discount|price) - Фильтр по типу события

## Магазины

### GET /stores
Получить список магазинов.

```json
// Response
{
  "items": [
    {
      "id": "hobbygames",
      "name": "Hobby Games",
      "site_url": "https://hobbygames.ru",
      "region": "RU",
      "currency": "RUB",
      "description": "Крупный магазин настольных игр",
      "logo_url": "https://example.com/logo.png",
      "contact_email": "info@hobbygames.ru",
      "contact_phone": "+7 (495) 123-45-67",
      "address": "Москва, ул. Тверская, 1",
      "working_hours": "10:00-21:00",
      "rating": 4.5,
      "is_active": true,
      "priority": 10,
      "shipping_info": "Доставка по РФ",
      "payment_methods": '["card", "cash", "online"]',
      "social_links": '{"vk": "https://vk.com/hobbygames"}'
    }
  ],
  "total": 1
}
```

### POST /stores
Добавить новый магазин.

## Агенты

### GET /agents
Получить список агентов с информацией о статусе.

```json
// Response
{
  "items": [
    {
      "id": "hobbygames_coming_soon",
      "name": "Hobby Games — Coming Soon",
      "type": "html",
      "schedule": {
        "cron": "0 */2 * * *",
        "timezone": "Europe/Moscow"
      },
      "rate_limit": {
        "rps": 0.3,
        "burst": 1,
        "daily_pages_cap": 50
      },
      "config": {
        "start_urls": ["https://hobbygames.ru/coming-soon"],
        "selectors": {
          "item": ".product-item",
          "title": ".product-item__title",
          "price": ".product-item__price",
          "url": "a.product-item__link::attr(href)"
        }
      },
      "enabled": true,
      "last_run": "2024-01-01T12:00:00Z",
      "last_status": "success",
      "pages_today": 25,
      "events_created": 150,
      "error_count": 0,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /agents
Создать нового агента.

```json
// Request
{
  "id": "new_store_agent",
  "name": "New Store Agent",
  "type": "html",
  "schedule": {
    "cron": "0 */4 * * *",
    "timezone": "Europe/Moscow"
  },
  "rate_limit": {
    "rps": 0.2,
    "burst": 1,
    "daily_pages_cap": 30
  },
  "config": {
    "start_urls": ["https://store.com/catalog"],
    "selectors": {
      "item": ".product-card",
      "title": ".product-title",
      "price": ".price",
      "url": "a.product-link::attr(href)"
    }
  },
  "enabled": true
}
```

### PUT /agents/{id}
Обновить конфигурацию агента.

### DELETE /agents/{id}
Удалить агента.

### POST /agents/{id}/run
Запустить агента вручную.

```json
// Response
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "started",
  "message": "Агент запущен вручную"
}
```

### POST /agents/import
Импортировать агента из ZIP архива.

**Request:** `multipart/form-data`
- `file`: ZIP архив с манифестом и кодом агента

### GET /agents/{id}/export
Экспортировать агента в ZIP архив.

## События

### GET /events
Получить ленту событий с фильтрацией.

**Query Parameters:**
- `skip`: int (default: 0) - Количество записей для пропуска
- `limit`: int (default: 50, max: 1000) - Количество записей на странице
- `game_id`: string - Фильтр по игре
- `store_id`: string - Фильтр по магазину
- `kind`: string (announce|preorder|release|discount|price) - Фильтр по типу события
- `from`: string (ISO datetime) - Начальная дата
- `to`: string (ISO datetime) - Конечная дата
- `min_discount`: number (минимальная скидка %)
- `max_price`: number (максимальная цена)
- `in_stock`: boolean - Фильтр по наличию

```json
// Response
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "game_id": "550e8400-e29b-41d4-a716-446655440001",
      "store_id": "hobbygames",
      "kind": "preorder",
      "title": "Громкое дело",
      "edition": "Базовая игра",
      "price": 2500.00,
      "currency": "RUB",
      "discount_pct": null,
      "in_stock": true,
      "start_at": "2024-02-01T00:00:00Z",
      "end_at": null,
      "url": "https://hobbygames.ru/gromkoe-delo",
      "source_id": "hobbygames_coming_soon",
      "signature_hash": "abc123...",
      "meta": {},
      "created_at": "2024-01-01T12:00:00Z",
      "game": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "title": "Громкое дело",
        "publisher": "Hobby Games"
      },
      "store": {
        "id": "hobbygames",
        "name": "Hobby Games"
      }
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50,
  "has_next": false,
  "has_prev": false,
  "pages_total": 1,
  "current_page": 1
}
```

### GET /events/{id}
Получить детальную информацию о событии.

## История цен

### GET /prices
Получить историю цен для графиков.

**Query Parameters:**
- `game_id`: string (обязательный)
- `store_id`: string[] (фильтр по магазинам)
- `from`: string (ISO datetime)
- `to`: string (ISO datetime)

```json
// Response
{
  "game_id": "550e8400-e29b-41d4-a716-446655440001",
  "data": [
    {
      "store_id": "hobbygames",
      "store_name": "Hobby Games",
      "prices": [
        {
          "observed_at": "2024-01-01T00:00:00Z",
          "price": 2500.00,
          "currency": "RUB"
        },
        {
          "observed_at": "2024-01-02T00:00:00Z",
          "price": 2250.00,
          "currency": "RUB"
        }
      ]
    }
  ],
  "total_points": 2
}
```

### GET /prices/export/csv
Экспортировать историю цен в CSV.

**Query Parameters:** те же, что и для `/prices`

**Response:** `text/csv` с заголовками `observed_at,store_id,store_name,price,currency`

## Правила уведомлений

### GET /rules
Получить список правил уведомлений.

```json
// Response
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Громкое дело - релиз",
      "logic": "OR",
      "conditions": [
        {
          "field": "game",
          "op": "in",
          "value": ["Громкое дело", "Gromkoe Delo"]
        },
        {
          "field": "title",
          "op": "contains_any",
          "value": ["предзаказ", "в продаже", "release", "preorder"]
        }
      ],
      "channels": ["webpush", "telegram"],
      "cooldown_hours": 12,
      "enabled": true,
      "last_triggered": "2024-01-01T12:00:00Z",
      "notification_count": 5,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /rules
Создать новое правило уведомлений.

```json
// Request
{
  "name": "Скидки более 20%",
  "logic": "AND",
  "conditions": [
    {
      "field": "discount_pct",
      "op": ">=",
      "value": 20
    },
    {
      "field": "store_id",
      "op": "in",
      "value": ["hobbygames", "lavkaigr"]
    }
  ],
  "channels": ["webpush"],
  "cooldown_hours": 6,
  "enabled": true
}
```

### PUT /rules/{id}
Обновить правило.

### DELETE /rules/{id}
Удалить правило.

### POST /rules/{id}/test
Протестировать правило на последних событиях.

```json
// Response
{
  "rule_id": "550e8400-e29b-41d4-a716-446655440000",
  "rule_name": "Громкое дело - релиз",
  "matched_events": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "title": "Громкое дело - предзаказ",
      "store_id": "hobbygames",
      "kind": "preorder",
      "created_at": "2024-01-01T12:00:00Z"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "title": "Громкое дело - в продаже",
      "store_id": "lavkaigr",
      "kind": "release",
      "created_at": "2024-01-02T10:00:00Z"
    }
  ],
  "match_count": 2
}
```

## Экспорт и импорт

### GET /export/full
Полный экспорт базы данных.

**Response:** ZIP архив с файлами:
- `games.ndjson`
- `stores.ndjson`
- `listing_events.ndjson`
- `price_history.ndjson`
- `alert_rules.json`
- `sources.json`
- `version.json`
- `checksums.txt`

### POST /import/full
Импорт полной базы данных.

**Request:** `multipart/form-data`
- `file`: ZIP архив
- `dry_run`: boolean (default: false)

```json
// Response (dry_run=true)
{
  "dry_run": true,
  "summary": {
    "games": {"added": 5, "updated": 3, "skipped": 10},
    "stores": {"added": 1, "updated": 0, "skipped": 5},
    "events": {"added": 150, "updated": 0, "skipped": 0},
    "rules": {"added": 2, "updated": 1, "skipped": 0}
  },
  "warnings": [
    "Игры с похожими названиями будут пропущены в реальном импорте"
  ],
  "errors": []
}
```

## Настройки

### GET /settings/notifications
Получить настройки уведомлений.

```json
// Response
{
  "webpush": {
    "vapid_public_key": "BM...PublicKey",
    "vapid_private_key": "encrypted_value",
    "vapid_email": "admin@example.com"
  },
  "telegram": {
    "bot_token": "encrypted_value",
    "chat_id": "encrypted_value",
    "enabled": false
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00"
  }
}
```

### PUT /settings/notifications
Обновить настройки уведомлений.

### POST /notifications/test/webpush
Отправить тестовое Web Push уведомление.

### POST /notifications/test/telegram
Отправить тестовое Telegram уведомление.

## Мониторинг

### GET /metrics
Получить метрики системы (Prometheus формат).

```text
# HELP agent_runs_total Total number of agent runs
# TYPE agent_runs_total counter
agent_runs_total{agent_id="hobbygames_coming_soon",status="success"} 150
agent_runs_total{agent_id="hobbygames_coming_soon",status="error"} 2

# HELP events_created_total Total number of events created
# TYPE events_created_total counter
events_created_total{kind="announce"} 45
events_created_total{kind="preorder"} 30
events_created_total{kind="release"} 25
events_created_total{kind="discount"} 50
events_created_total{kind="price"} 200
```

### GET /dashboard
Получить данные для дашборда.

```json
// Response
{
  "summary": {
    "total_games": 156,
    "total_stores": 8,
    "active_agents": 11,
    "events_today": 25,
    "notifications_today": 5
  },
  "recent_events": [...],
  "agent_status": [...],
  "price_changes": [...],
  "system_health": {
    "database": "healthy",
    "redis": "healthy",
    "minio": "healthy",
    "celery": "healthy"
  }
}
```

## LLM интеграция

### GET /llm/models
Получить список доступных моделей Ollama.

```json
// Response
{
  "models": [
    {
      "name": "llama2",
      "size": "3.8GB",
      "modified_at": "2024-01-01T00:00:00Z"
    },
    {
      "name": "mistral",
      "size": "4.1GB",
      "modified_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST /llm/extract
Извлечь данные из текста с помощью LLM.

```json
// Request
{
  "text": "Настольная игра 'Громкое дело' предзаказ 2500₽",
  "model": "llama2"
}

// Response
{
  "game_title": "Громкое дело",
  "kind": "preorder",
  "price_rub": 2500,
  "discount_pct": null,
  "in_stock": true,
  "edition": null
}
```

## Ошибки

### Стандартные HTTP коды
- `200 OK`: Успешное выполнение
- `201 Created`: Ресурс создан
- `400 Bad Request`: Неверный запрос
- `401 Unauthorized`: Требуется аутентификация
- `403 Forbidden`: Нет доступа
- `404 Not Found`: Ресурс не найден
- `422 Unprocessable Entity`: Ошибка валидации
- `429 Too Many Requests`: Превышен лимит запросов
- `500 Internal Server Error`: Внутренняя ошибка сервера

### Формат ответа с ошибкой
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Неверный формат данных",
    "details": {
      "field": "price",
      "reason": "значение должно быть положительным числом"
    }
  }
}
```

## Ограничения

- **API Rate Limit**: 100 запросов/минута для пользователя
- **Пагинация**: Максимальный размер страницы 100 элементов
- **Экспорт**: Раз в час для полного экспорта БД
- **Тестовые уведомления**: 5 в минуту
- **LLM вызовы**: 10 в минуту