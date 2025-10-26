# Настройка окружения разработки

## Системные требования

- **Docker** и **Docker Compose** последней версии
- **Python** 3.11+ (для локальной разработки)
- **Node.js** 18+ и **npm** 9+ (для фронтенда)
- **Git**
- **VS Code** (рекомендуется) или другой редактор кода

## Клонирование и первичная настройка

```bash
# Клонирование репозитория
git clone <repository-url>
cd BGW

# Копирование файла окружения
cp .env.example .env

# Редактирование конфигурации
nano .env
```

## Переменные окружения (.env)

```bash
# Часовой пояс
TZ=Europe/Moscow

# База данных
DATABASE_URL=postgresql+psycopg2://app:app@postgres:5432/app

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO хранилище
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=raw
S3_SECURE=false

# Ollama LLM
OLLAMA_URL=http://host.docker.internal:11434

# Лимиты
MAX_DAILY_PAGES=1000
DEFAULT_RPS=0.3
DEFAULT_BURST=1

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Web Push (VAPID)
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_EMAIL=admin@example.com

# Безопасность
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

## Запуск через Docker Compose (рекомендуется)

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Логи конкретного сервиса
docker-compose logs -f api

# Остановка
docker-compose down

# Пересборка с кэшем
docker-compose up -d --build

# Полная пересборка без кэша
docker-compose up -d --build --no-cache
```

## Доступ к сервисам

| Сервис | URL | Логин/Пароль |
|--------|-----|--------------|
| Frontend | http://localhost | - |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| MinIO Console | http://localhost:9001 | minioadmin/minioadmin |
| PostgreSQL | localhost:5432 | app/app |
| Redis | localhost:6379 | - |
| Prometheus | http://localhost:9090 | - |
| Grafana | http://localhost:3001 | admin/admin |

## Локальная разработка

### Backend разработка

```bash
# Переход в директорию бэкенда
cd backend

# Создание виртуального окружения
python -m venv venv

# Активация (Linux/Mac)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запуск Celery worker (в другом терминале)
celery -A app.celery_app worker -l INFO

# Запуск Celery beat (в третьем терминале)
celery -A app.celery_app beat -l INFO
```

### Миграции базы данных

```bash
# Создание новой миграции
alembic revision --autogenerate -m "описание изменений"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1

# История миграций
alembic history

# Текущая версия
alembic current
```

### Frontend разработка

```bash
# Переход в директорию фронтенда
cd frontend

# Установка зависимостей
npm install

# Запуск dev сервера
npm run dev

# Сборка для production
npm run build

# Линтинг
npm run lint

# Исправление linting ошибок
npm run lint:fix

# Типизация
npm run type-check
```

## Структура проекта

```
BGW/
├── backend/                    # FastAPI бэкенд
│   ├── app/
│   │   ├── agents/            # Агентная платформа
│   │   │   ├── base.py        # Базовые классы агентов
│   │   │   ├── registry.py    # Реестр агентов
│   │   │   └── builtin/       # Встроенные агенты
│   │   ├── api/               # FastAPI роуты
│   │   │   ├── auth.py        # Аутентификация
│   │   │   ├── games.py       # Управление играми
│   │   │   ├── agents.py      # Управление агентами
│   │   │   └── ...
│   │   ├── core/              # Ядро приложения
│   │   │   ├── config.py      # Конфигурация
│   │   │   ├── database.py    # Подключение к БД
│   │   │   └── security.py    # Безопасность
│   │   ├── models/            # SQLAlchemy модели
│   │   │   ├── base.py        # Базовые модели
│   │   │   ├── game.py        # Модель игры
│   │   │   └── ...
│   │   ├── schemas/           # Pydantic схемы
│   │   ├── services/          # Бизнес-логика
│   │   │   ├── agent_service.py
│   │   │   └── notification_service.py
│   │   ├── tasks/             # Celery задачи
│   │   │   ├── agents.py      # Задачи агентов
│   │   │   └── notifications.py
│   │   ├── main.py            # FastAPI приложение
│   │   └── celery_app.py      # Celery конфигурация
│   ├── alembic/               # Миграции БД
│   ├── tests/                 # Тесты
│   ├── requirements.txt       # Зависимости Python
│   └── Dockerfile             # Docker конфигурация
├── frontend/                  # React фронтенд
│   ├── src/
│   │   ├── components/        # React компоненты
│   │   │   ├── Layout/        # Компоновка
│   │   │   ├── GameForm/      # Форма игры
│   │   │   └── ...
│   │   ├── pages/             # Страницы приложения
│   │   │   ├── Dashboard.tsx  # Дашборд
│   │   │   ├── Games.tsx      # Управление играми
│   │   │   └── ...
│   │   ├── services/          # API клиенты
│   │   │   ├── api.ts         # Base API клиент
│   │   │   └── games.ts       # Игры API
│   │   ├── store/             # Zustand state
│   │   │   ├── authStore.ts   # Аутентификация
│   │   │   └── gamesStore.ts  # Игры
│   │   ├── utils/             # Утилиты
│   │   └── types/             # TypeScript типы
│   ├── public/                # Статические файлы
│   ├── package.json           # Зависимости npm
│   └── Dockerfile             # Docker конфигурация
├── deploy/                    # Конфигурация деплоя
│   ├── nginx.conf             # Nginx конфигурация
│   ├── prometheus.yml         # Prometheus конфиг
│   └── grafana/               # Grafana дашборды
├── docs/                      # Документация
├── docker-compose.yml         # Docker Compose конфиг
├── .env.example              # Пример окружения
└── README.md                 # Описание проекта
```

## Разработка агентов

### Создание нового агента

1. **Создать файл агента** в `backend/app/agents/builtin/`:

```python
# backend/app/agents/builtin/newstore.py
from bs4 import BeautifulSoup
import re
from typing import AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft

class NewStoreAgent(HTMLAgent):
    """Агент для New Store."""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Извлечение данных
        items = soup.select(self.selectors.get('item', '.product'))

        for item in items:
            title = item.select_one(self.selectors.get('title', '.title'))
            price = item.select_one(self.selectors.get('price', '.price'))
            url = item.select_one(self.selectors.get('url', 'a'))

            if title:
                yield ListingEventDraft(
                    title=title.get_text(strip=True),
                    price=self._extract_price(price),
                    url=url.get('href') if url else None,
                    kind='price'  # или другой тип
                )

    def _extract_price(self, price_elem):
        if not price_elem:
            return None
        price_text = price_elem.get_text(strip=True)
        match = re.search(r'(\d[\d\s]*)\s*₽', price_text)
        return float(match.group(1).replace(' ', '')) if match else None
```

2. **Зарегистрировать агент** в `backend/app/agents/builtin/__init__.py`:

```python
from .newstore import NewStoreAgent

AGENT_REGISTRY = {
    # ... другие агенты
    'newstore': NewStoreAgent,
}
```

3. **Создать миграцию** для добавления агента в БД:

```python
# alembic/versions/xxx_add_newstore_agent.py
def upgrade():
    # Добавление агента в таблицу source_agent
    pass
```

### Тестирование агентов

```python
# backend/tests/test_agents.py
import pytest
from app.agents.builtin.newstore import NewStoreAgent

@pytest.mark.asyncio
async def test_newstore_agent():
    agent = NewStoreAgent(
        config={'selectors': {'item': '.product'}},
        secrets={},
        ctx=MockContext()
    )

    # Тестирование с примером HTML
    with open('tests/fixtures/newstore_page.html') as f:
        html_content = f.read()

    fetched = Fetched(
        url='https://newstore.com/catalog',
        status=200,
        body=html_content,
        headers={},
        fetched_at=datetime.now()
    )

    events = []
    async for event in agent.parse(fetched):
        events.append(event)

    assert len(events) > 0
    assert events[0].title is not None
```

## Работа с базой данных

### Подключение к БД

```bash
# Через Docker
docker-compose exec postgres psql -U app -d app

# Локально (если PostgreSQL установлен)
psql postgresql://app:app@localhost:5432/app
```

### Полезные SQL запросы

```sql
-- Список всех игр
SELECT id, title, publisher, bgg_id FROM game ORDER BY title;

-- Последние события
SELECT le.title, le.kind, s.name as store_name, le.created_at
FROM listing_event le
JOIN store s ON le.store_id = s.id
ORDER BY le.created_at DESC LIMIT 10;

-- Статус агентов
SELECT id, name, enabled, created_at FROM source_agent;

-- История цен для игры
SELECT * FROM price_history WHERE game_id = 'uuid' ORDER BY observed_at DESC;
```

## Тестирование

### Запуск тестов

```bash
# Backend тесты
cd backend
pytest

# С покрытием
pytest --cov=app

# Конкретный тест
pytest tests/test_agents.py::test_newstore_agent -v

# Frontend тесты
cd frontend
npm test

# E2E тесты (если настроены)
npm run test:e2e
```

### Написание тестов

```python
# backend/tests/test_game_service.py
import pytest
from app.services.game_service import GameService
from app.models.game import Game

@pytest.fixture
async def game_service():
    return GameService()

@pytest.mark.asyncio
async def test_create_game(game_service):
    game_data = {
        'title': 'Тестовая игра',
        'publisher': 'Тестовый издатель'
    }

    game = await game_service.create_game(game_data)

    assert game.title == 'Тестовая игра'
    assert game.publisher == 'Тестовый издатель'
    assert game.id is not None
```

## Отладка

### Backend отладка

```python
# В коде
import logging
logger = logging.getLogger(__name__)

logger.info("Информационное сообщение")
logger.debug("Отладочное сообщение")
logger.error("Ошибка")

# Отладка в VS Code
# .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: FastAPI",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/backend/app/main.py",
            "console": "integratedTerminal",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/backend"
            }
        }
    ]
}
```

### Frontend отладка

```typescript
// В компоненте
console.log('Отладочная информация', data);

// React DevTools
// Redux DevTools (если используется Redux)

// Отладка в VS Code
// .vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Launch Chrome against localhost",
            "type": "chrome",
            "request": "launch",
            "url": "http://localhost:3000",
            "webRoot": "${workspaceFolder}/frontend/src"
        }
    ]
}
```

## Линтинг и форматирование

### Backend

```bash
# Установка инструментов
pip install black isort flake8 mypy

# Форматирование кода
black app/
isort app/

# Проверка стиля
flake8 app/

# Типизация
mypy app/

# Pre-commit hook
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
```

### Frontend

```bash
# Линтинг
npm run lint

# Исправление
npm run lint:fix

# TypeScript проверка
npm run type-check

# Prettier форматирование
npx prettier --write src/
```

## Производительность

### Backend оптимизация

```python
# Индексы в БД
# В моделях SQLAlchemy
from sqlalchemy import Index

class ListingEvent(BaseModel):
    __tablename__ = "listing_event"

    # ...

    __table_args__ = (
        Index('idx_game_created', 'game_id', 'created_at'),
        Index('idx_store_kind', 'store_id', 'kind'),
    )

# Кэширование Redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@cached(expire=60)
async def get_games():
    return await game_service.get_all_games()
```

### Frontend оптимизация

```typescript
// React.memo для компонентов
const GameCard = React.memo(({ game }: { game: Game }) => {
    return <div>{game.title}</div>;
});

// useMemo для вычислений
const expensiveValue = useMemo(() => {
    return computeExpensiveValue(data);
}, [data]);

// useCallback для функций
const handleClick = useCallback((id: string) => {
    onClick(id);
}, [onClick]);
```

## Полезные команды

```bash
# Проверка статуса контейнеров
docker-compose ps

# Вход в контейнер
docker-compose exec api bash

# Просмотр логов в реальном времени
docker-compose logs -f api worker

# Перезапуск конкретного сервиса
docker-compose restart api

# Очистка Docker
docker system prune -a

# Резервное копирование БД
docker-compose exec postgres pg_dump -U app app > backup.sql

# Восстановление БД
docker-compose exec -T postgres psql -U app app < backup.sql
```

## Часовой пояс и локализация

```python
# Настройка часового пояса
import pytz
from datetime import datetime

moscow_tz = pytz.timezone('Europe/Moscow')
now_moscow = datetime.now(moscow_tz)

# Локализация в фронтенде
import dayjs from 'dayjs';
import 'dayjs/locale/ru';

dayjs.locale('ru');
```

## Работа с миграциями

```bash
# Создание миграции после изменений в моделях
alembic revision --autogenerate -m "Add new fields to Game model"

# Проверка сгенерированной миграции
alembic upgrade head
alembic downgrade -1

# Применение в production
docker-compose exec api alembic upgrade head
```