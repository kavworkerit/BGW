# Архитектура системы мониторинга настольных игр (BGW)

## Обзор проекта

BGW - это локальная однопользовательская система для мониторинга релизов, предзаказов и скидок на настольные игры из различных интернет-магазинов и источников.

## Ключевые характеристики

- **Тип приложения**: Локальное однопользовательское веб-приложение
- **Язык интерфейса**: Русский
- **Ограничения**: до 100 источников, до 1000 страниц/сутки, хранение данных 2 года
- **Деплой**: Docker Compose + OneClick PowerShell скрипт
- **LLM интеграция**: Ollama сервер (отдельный сервис)

## Сервисная архитектура

### Основные сервисы (Docker Compose)

| Сервис | Технология | Назначение |
|--------|------------|-----------|
| `api` | FastAPI (Python 3.11+) | REST API, бизнес-логика |
| `worker` | Celery | Фоновые задачи (парсинг, обработка) |
| `beat` | Celery Beat | Планировщик задач |
| `postgres` | PostgreSQL 15 + TimescaleDB | Основная БД + временные ряды |
| `redis` | Redis 7 | Брокер очередей + кэш |
| `minio` | MinIO S3 | Хранение сырых данных (HTML/JSON) |
| `frontend` | React + TypeScript | Пользовательский интерфейс |
| `nginx` | Nginx | Reverse proxy |
| `prometheus` | Prometheus | Сбор метрик |
| `grafana` | Grafana | Визуализация метрик |
| `backup` | Cron job | Ежедневные бэкапы |

### Внешние зависимости

- **Ollama**: `host.docker.internal:11434` (отдельный сервис)
- **Telegram**: Опционально для уведомлений
- **Web Push**: VAPID для браузерных уведомлений

## Модель данных

### Основные сущности

#### Игры (Game)
```python
Game:
  id: UUID (PK)
  title: String(500)
  synonyms: Array<String>
  bgg_id: String(50)  # BoardGameGeek ID
  publisher: String(200)
  tags: Array<String>
  description: Text
  min_players, max_players: Integer
  min_playtime, max_playtime: Integer  # в минутах
  year_published: Integer
  language: String(10)  # RU, EN, etc.
  complexity: Float  # 1-5
  image_url: String(500)
  rating_bgg: Float
  rating_users: Float
```

#### Магазины (Store)
```python
Store:
  id: String(100) (PK)
  name: String(200)
  site_url: String(500)
  region: String(10)  # RU
  currency: String(3)  # RUB
  description: Text
  logo_url: String(500)
  contact_email, contact_phone: String
  address: Text
  working_hours: Text
  rating: Float
  is_active: Boolean
  priority: Integer
  shipping_info: Text
  payment_methods: String(500)  # JSON
  social_links: Text  # JSON
```

#### События (ListingEvent)
```python
ListingEvent:
  id: UUID (PK)
  game_id: UUID (FK)
  store_id: String(100) (FK)
  kind: EventKind  # ENUM(announce, preorder, release, discount, price)
  title: String(500)
  edition: String(200)
  price: Numeric(12,2)
  currency: String(3)
  discount_pct: Numeric(5,2)
  in_stock: Boolean
  start_at, end_at: DateTime
  url: Text
  source_id: String (FK)
  signature_hash: String(64)  # дедупликация
  meta: JSONB
```

#### История цен (PriceHistory)
```python
PriceHistory:  # TimescaleDB hypertable
  game_id: UUID (FK, PK)
  store_id: String(100) (FK, PK)
  observed_at: DateTime (PK)
  price: Numeric(12,2)
  currency: String(3)
```

#### Агенты источников (SourceAgent)
```python
SourceAgent:
  id: String (PK)
  name: String(255)
  type: String(50)  # ENUM(api, html, headless, telegram_public)
  schedule: JSON
  rate_limit: JSON
  config: JSON
  enabled: Boolean
```

#### Правила уведомлений (AlertRule)
```python
AlertRule:
  id: UUID (PK)
  name: String(255)
  logic: String(10)  # AND/OR
  conditions: JSON
  channels: Array<String>  # [webpush, telegram]
  cooldown_hours: String(10)
  enabled: Boolean
```

## Агентная платформа

### Типы агентов

1. **HTMLAgent**: Веб-скрапинг с CSS селекторами
2. **APIAgent**: Работа с REST API
3. **HeadlessAgent**: Парсинг динамических сайтов (Playwright/Selenium)
4. **TelegramAgent**: Мониторинг публичных каналов

### Интерфейс агента

```python
class BaseAgent:
    TYPE: str  # 'api', 'html', 'headless', 'telegram_public'
    CONFIG_SCHEMA: dict  # JSON Schema

    def __init__(self, config: dict, secrets: dict, ctx: RuntimeContext):
        pass

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение данных с учетом лимитов и robots.txt"""
        pass

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечение черновых событий"""
        pass
```

### Манифест агента

```json
{
  "version": "1.0",
  "id": "hobbygames_coming_soon",
  "name": "Hobby Games — Coming Soon",
  "type": "html",
  "entrypoint": "agent.py",
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
  "secrets": {}
}
```

## Пайплайн обработки данных

### 1. Сбор данных
- Планировщик запускает агентов по расписанию
- Учет квот: `daily_pages_cap`, `rps`, `burst`
- Сохранение сырых данных в MinIO
- Дедупликация по hash

### 2. Парсинг
- Извлечение черновых событий `ListingEventDraft`
- Нормализация и очистка данных
- Определение типа события (announce/preorder/release/discount/price)

### 3. Нормализация названия игр
- Очистка от мусорных слов
- Fuzzy matching с базой игр
- Использование синонимов
- Опциональное уточнение через LLM

### 4. Обогащение данных
- Привязка к `game_id` и `store_id`
- Определение валюты и региона
- Расчет скидок

### 5. Дедупликация
```python
signature_hash = sha256(
    f"{normalize(title)}|{store_id}|{normalize(edition)}|{round_price}|{date_bucket}"
)
```

### 6. Сохранение
- Создание `ListingEvent`
- Запись в `PriceHistory` (TimescaleDB)
- Триггер правил уведомлений

## API архитектура

### Основные эндпоинты

| Группа | Эндпоинты | Назначение |
|--------|-----------|-----------|
| **Игры** | `GET/POST/PUT/DELETE /games` | Управление watchlist |
| **Магазины** | `GET/POST /stores` | Управление источниками |
| **Агенты** | `GET/POST/PUT/DELETE /agents` | Управление агентами |
| **События** | `GET /events` | Лента событий с фильтрами |
| **Правила** | `GET/POST/PUT/DELETE /rules` | Правила уведомлений |
| **Цены** | `GET /prices` | История цен для графиков |
| **Экспорт** | `GET /export/full` | Полный экспорт БД |
| **Настройки** | `GET/PUT /settings/*` | Конфигурация системы |

### Аутентификация
- Локальная однопользовательская
- JWT токены
- Опционально можно расширить до многопользовательской

## Система уведомлений

### Каналы доставки
1. **Web Push**: VAPID для браузерных уведомлений
2. **Telegram**: Бот для推送 уведомлений (опционально)

### Правила уведомлений
```json
{
  "logic": "OR",
  "conditions": [
    {"field": "game", "op": "in", "value": ["Громкое дело"]},
    {"field": "title", "op": "contains_any", "value": ["предзаказ", "в продаже"]}
  ],
  "channels": ["webpush", "telegram"],
  "cooldown_hours": 12,
  "enabled": true
}
```

### Подавление дубликатов
- Коoldown периоды
- Проверка по `signature_hash`
- Глобальные "тихие часы"

## Мониторинг и метрики

### Prometheus метрики
- `agent_runs_total{agent_id,status}`
- `agent_pages_fetched_total{agent_id}`
- `events_created_total{kind}`
- `notifications_sent_total{channel,status}`
- `llm_calls_total{result}`
- `event_dedup_ratio`

### Grafana дашборды
- Статус агентов
- Сбор событий
- Доставка уведомлений
- Использование квот

## Безопасность

### Локальное развертывание
- Однопользовательский режим
- Локальное хранение секретов
- Опциональный HTTPS
- Соблюдение robots.txt

### Управление секретами
- `.secrets.json` (локально)
- Пустые secrets в манифестах
- Ввод через UI

## Разработка и тестирование

### Структура кода
```
backend/
├── app/
│   ├── agents/          # Агентная платформа
│   ├── api/             # FastAPI роуты
│   ├── models/          # SQLAlchemy модели
│   ├── services/        # Бизнес-логика
│   ├── tasks/           # Celery задачи
│   └── core/            # Конфигурация
frontend/
├── src/
│   ├── components/      # React компоненты
│   ├── pages/           # Страницы приложения
│   ├── services/        # API клиенты
│   └── store/           # Zustand state
```

### Тестирование
- Unit тесты для агентов
- Record/Replay для HTML (VCR.py)
- Тесты нормализации названий
- E2E тесты для критических путей

## Деплоймент

### Docker Compose
```yaml
services:
  api:
    build: ./backend
    env_file: .env
    depends_on: [postgres, redis, minio]

  worker:
    build: ./backend
    command: celery -A app.celery_app worker -l INFO
    depends_on: [api, redis, postgres]

  frontend:
    build: ./frontend
    depends_on: [api]
```

### Автоматический деплой
- PowerShell OneClick скрипт
- Выкачивание репозитория
- Запуск в Docker
- Первичная инициализация

## Масштабирование и ограничения

### Текущие ограничения
- 100 источников (агентов)
- 1000 страниц/сутки
- Хранение 2 года
- Однопользовательский режим

### Пути расширения
1. **Горизонтальное масштабирование**: несколько worker'ов
2. **Вертикальное масштабирование**: увеличение квот
3. **Функциональное**: многопользовательский режим, новые источники
4. **Географическое**: другие регионы и языки

## Резервное копирование и восстановление

### Ежедневные бэкапы
- PostgreSQL dump
- Минимальные файлы из MinIO
- Конфигурации агентов
- ZIP архив с датой

### Восстановление
- `docker-compose down`
- Восстановление БД из dump
- Перезапуск сервисов
- Проверка целостности данных