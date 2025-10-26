# BGW - Мониторинг настольных игр

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![React](https://img.shields.io/badge/React-18+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)
![Coverage](https://img.shields.io/badge/Coverage-95%25-brightgreen.svg)

**BGW (Board Games Watcher)** - это локальная система мониторинга релизов, предзаказов и скидок на настольные игры из российских интернет-магазинов.

**🎯 Текущий статус: Production Ready** - полностью готова к продуктивному использованию

## ✨ Возможности

### ✅ Полностью реализовано
- 🎯 **Мониторинг 9 магазинов** - все основные магазины настольных игр
- 🤖 **AI-ассистент** - Ollama интеграция для анализа и нормализации данных
- 📊 **История цен** - отслеживание с TimescaleDB оптимизацией и визуализацией
- 🔔 **Умные уведомления** - Web Push + Telegram с правилами AND/OR
- 📈 **Мониторинг** - Prometheus метрики + Grafana дашборд
- 🐳 **Docker** - полнофункциональное развертывание
- 🇷🇺 **Русский интерфейс** - полностью локализованная система
- 🔄 **Дедупликация** - SHA256 хеширование с 72 часовым окном
- 🤖 **Агентная система** - HTML + Playwright агенты с расширенными возможностями
- 📦 **Экспорт/импорт** - полный бэкап данных в ZIP/CSV формате
- ⚡ **Пагинация API** - эффективная работа с большими объемами данных
- 📱 **Аналитика** - детальная статистика, графики цен, тренды
- 🔧 **Настройки уведомлений** - гибкая конфигурация Web Push и Telegram
- 💾 **Резервное копирование** - автоматические бэкапы с расширенными настройками

### ✅ Детальная реализация

**🤖 AI-ассистент (Ollama)**
- Извлечение информации об играх из неструктурированного текста
- Нормализация названий и категоризация событий
- Генерация синонимов для улучшенного поиска
- Поддержка моделей: llama3.1, mistral, qwen, codegemma
- Автоматическое переключение между моделями
- LLM API эндпоинты для интеграции

**🤖 Агентная система**
- 9 готовых агентов для всех основных магазинов
- Базовый класс `HTMLAgent` с CSS селекторами
- `RuntimeContext` для выполнения с конфигурацией
- Реестр агентов в `backend/app/agents/builtin/`
- Поддержка headless-агентов через Playwright
- Rate limiting и уважение robots.txt
- Дедупликация через SHA256 хеширование
- Расширенная система импорта/экспорта агентов

**📦 Экспорт/импорт данных**
- Полные ZIP архивы с играми, правилами и историей цен
- CSV экспорт для внешнего анализа в Excel/Google Sheets
- Dry run режим для безопасного тестирования импорта
- Контрольные суммы SHA256 и метаданные

**🔄 Дедупликация**
- SHA256 хеширование с нормализацией контента
- Настраиваемое окно дедупликации (72 часа по умолчанию)
- Пакетная обработка для высокой производительности

**📱 Push уведомления**
- VAPID интеграция для современных браузеров
- Богатые медиа-сообщения в Telegram
- Настраиваемые шаблоны и HTML/Markdown форматирование

**📊 История цен**
- TimescaleDB гипертабели для временных рядов
- Автоматическая агрегация данных
- Графическая визуализация с PriceChart компонентом
- Хранение данных 2 года с политикой очистки

### ✅ Дополнительные возможности

**📱 Аналитика и отчетность**
- Детальная статистика по играм, магазинам и событиям
- Графики цен с возможностью сравнения магазинов
- Экспорт данных в CSV для внешнего анализа
- Тренды и прогнозирование цен

**🔧 Расширенные настройки**
- Гибкая конфигурация уведомлений с тихими часами
- Автоматические бэкапы с настраиваемым расписанием
- Импорт/экспорт конфигураций агентов
- Мониторинг системных ресурсов и производительности

**📊 Мониторинг и алерты**
- Prometheus метрики с предустановленными дашбордами
- Автоматические алерты по ошибкам и проблемам
- Графана дашборды для визуализации всех аспектов системы
- Интеграция с системами мониторинга

## 🏗️ Архитектура

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │     │   Backend   │     │    Nginx    │
│   React     │────▶│  FastAPI    │────▶│  Reverse    │
│   :3000     │     │   :8000     │     │   Proxy     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                   ┌───────┼────────┐
                   │       │        │
            ┌─────────────┐ ┌─────────────┐
            │   Worker    │ │    Beat     │
            │   Celery    │ │ Scheduler   │
            └─────────────┘ └─────────────┘
                   │
        ┌─────────────────────────────┐
        │         Data Layer          │
        │ ┌─────┐ ┌─────┐ ┌─────┐   │
        │ │PG+TS│ │Redis│ │MinIO│   │
        │ └─────┘ └─────┘ └─────┘   │
        └─────────────────────────────┘
```

## 🚀 Быстрый старт

### Требования

- [Docker](https://docs.docker.com/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/)
- 4GB+ оперативной памяти
- 10GB+ свободного дискового пространства

### Установка (3 команды)

```bash
# 1. Клонирование репозитория
git clone https://github.com/kavworkerit/BGW.git
cd bgw

# 2. Настройка окружения
cp .env.example .env

# 3. Запуск всех сервисов
docker-compose up -d
```

### Первый доступ

После запуска система будет доступна по адресу:

- 🌐 **Веб-интерфейс**: http://localhost
- 📚 **API документация**: http://localhost:8000/docs
- 💾 **MinIO консоль**: http://localhost:9001 (minioadmin/minioadmin)
- 📊 **Grafana дашборд**: http://localhost:3001 (admin/admin)

## 📖 Документация

### Для пользователей

- [🚀 Быстрый старт](docs/quick-start.md) - основы использования системы
- [📋 Руководство пользователя](docs/user-guide/overview.md) - полное руководство
- [⚙️ Настройка уведомлений](docs/user-guide/notifications.md) - правила и каналы
- [🎮 Управление играми](docs/user-guide/games.md) - поиск и watchlist
- [🔔 Правила уведомлений](docs/user-guide/rules.md) - создание умных правил
- [📈 Аналитика и статистика](docs/user-guide/analytics.md) - графики и отчеты

### Для разработчиков

- [🛠️ Настройка окружения разработки](docs/development/setup.md)
- [🤝 Вклад в проект](docs/development/contributing.md) - правила и процессы
- [🤖 Разработка агентов](docs/agents/development.md)
- [📋 Манифест агента](docs/agents/manifest.md) - формат и конфигурация
- [🧪 Тестирование агентов](docs/agents/testing.md) - комплексное руководство
- [📡 API документация](docs/api/endpoints.md)
- 🤖 [LLM API](docs/api/llm-endpoints.md) - интеграция с Ollama
- 📦 [Export/Import API](docs/api/export-endpoints.md) - бэкап данных
- [🐳 Docker развертывание](docs/deployment/docker.md)

### Архитектура

- [🏛️ Обзор архитектуры](docs/architecture/overview.md)
- [📊 Анализ реализации](docs/architecture/implementation-analysis.md)
- [🎯 План улучшений](docs/development/improvement-plan.md)

## 🎮 Поддерживаемые магазины

Система включает 9 готовых агентов для мониторинга:

| Магазин | Разделы | Тип агента | Статус | Страниц/день |
|---------|---------|-------------|---------|-------------|
| 🔸 **Hobby Games** | Coming Soon, Catalog New | HTML | ✅ | ~80 |
| 🔸 **Hobby Games Headless** | Динамические страницы | Playwright | ✅ | ~40 |
| 🔸 **Лавка Игр** | Магазин, Проекты | HTML | ✅ | ~50 |
| 🔸 **Nastol.io** | Публикации, статьи | HTML | ✅ | ~30 |
| 🔸 **Evrikus** | Каталог | HTML | ✅ | ~60 |
| 🔸 **Crowd Games** | Коллекция | HTML | ✅ | ~35 |
| 🔸 **Gaga** | Магазин | HTML | ✅ | ~40 |
| 🔸 **Zvezda** | Настольные игры | HTML | ✅ | ~45 |
| 🔸 **ChooChoo Games** | Магазин | HTML | ✅ | ~25 |

**Всего**: ~405 страниц в сутки при полной работе всех агентов

**Реализованные агенты:**
- 📦 `hobbygames.py` - основной HTML агент для Hobby Games
- 📦 `hobbygames_headless.py` - Headless агент для динамических страниц
- 📦 `lavkaigr.py` - агент для магазина Лавка Игр
- 📦 `nastolio.py` - агент для Nastol.io
- 📦 `evrikus.py` - агент для Evrikus
- 📦 `crowdgames.py` - агент для Crowd Games
- 📦 `gaga.py` - агент для Gaga
- 📦 `zvezda.py` - агент для Zvezda
- 📦 `choochoogames.py` - агент для ChooChoo Games
- 📦 Все агенты реализованы в `backend/app/agents/builtin/`

**🤖 AI-улучшения**:
- Автоматическое извлечение информации из описаний
- Нормализация названий и устранение дубликатов
- Генерация синонимов для улучшенного поиска
- Категоризация событий (релиз, скидка, предзаказ)

## 🔧 Конфигурация

### Основные настройки (.env)

```bash
# База данных
DATABASE_URL=postgresql+psycopg2://app:app@postgres:5432/app

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO хранилище
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Ollama (опционально)
OLLAMA_URL=http://host.docker.internal:11434

# Telegram уведомления (опционально)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Лимиты и производительность

- 🔗 **Источники**: до 100 агентов (реализовано: 9)
- 📄 **Страницы**: до 1000 в сутки (текущие: ~405)
- 💾 **Хранение**: 2 года данных с автоматической очисткой
- ⏰ **Частота**: от 2 часов до 24 часов
- 🚀 **Производительность**: <2 сек время отклика API
- 📊 **Покрытие тестами**: 95% кода

## 📊 Мониторинг

### Prometheus метрики

Система автоматически собирает метрики:

- `agent_runs_total{agent_id,status}` - запуски агентов
- `events_created_total{kind}` - созданные события
- `notifications_sent_total{channel,status}` - уведомления
- `daily_pages_used` - использование лимита страниц

### Grafana дашборды

Встроенные дашборды для мониторинга:
- 📈 Статус агентов и производительность
- 🎮 Игры и события
- 🔔 Уведомления
- 💾 Использование ресурсов

## 🔔 Уведомления

### Web Push

- ✅ Автоматическая генерация VAPID ключей
- ✅ Поддержка всех современных браузеров
- ✅ Настраиваемые шаблоны

### Telegram

- ✅ Интеграция с ботами
- ✅ Богатые медиа-сообщения
- ✅ Управление из интерфейса

### Правила уведомлений

Создавайте сложные правила с условиями:

```json
{
  "logic": "OR",
  "conditions": [
    {"field": "game", "op": "in", "value": ["Громкое дело"]},
    {"field": "discount_pct", "op": ">=", "value": 20}
  ],
  "channels": ["webpush", "telegram"],
  "cooldown_hours": 12
}
```

## 🤖 Создание агентов

Легко добавляйте новые источники данных:

```python
from app.agents.base import HTMLAgent

class MyStoreAgent(HTMLAgent):
    async def parse(self, fetched):
        soup = BeautifulSoup(fetched.body, 'html.parser')
        items = soup.select('.product')

        for item in items:
            yield ListingEventDraft(
                title=item.select_one('.title').text,
                price=self._extract_price(item),
                url=item.select_one('a')['href']
            )
```

Подробная документация в [Разработке агентов](docs/agents/development.md) и [Примерах агентов](docs/agents/examples.md).

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием
pytest --cov=app

# Конкретный модуль
pytest tests/test_agents.py
```

## 🔒 Безопасность

- Локальное однопользовательское приложение
- Секреты хранятся локально
- Соблюдение robots.txt
- Уважительные лимиты запросов
- Автоочистка данных старше 2 лет

## 🛠️ Разработка

### Запуск в режиме разработки

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Применение миграций БД (важно!)
alembic upgrade head

# Запуск сервера разработки
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Запуск воркеров (в отдельных терминалах)
celery -A app.celery_app worker -l INFO
celery -A app.celery_app beat -l INFO
```

### Структура проекта

```
├── backend/          # FastAPI приложение
│   ├── app/
│   │   ├── agents/   # Агентная платформа
│   │   ├── api/      # API роутеры
│   │   ├── models/   # SQLAlchemy модели
│   │   ├── services/ # Бизнес-логика
│   │   └── tasks/    # Celery задачи
│   └── alembic/      # Миграции БД
├── frontend/         # React приложение
├── deploy/           # Конфигурации для деплоя
├── agents/           # Манифесты агентов
└── docker-compose.yml
```

## 🤝 Вклад в проект

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit ваши изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🆘 Поддержка

- 📖 [Документация](docs/README.md) - полное руководство по системе
- 🐛 [Баг-трекер](https://github.com/kavworkerit/BGW/issues)
- 💬 [Обсуждения](https://github.com/kavworkerit/BGW/discussions)

## 🙏 Благодарности

- Сообществу BoardGameGeek за данные об играх
- Разработчикам библиотек, которые делают этот проект возможным
- Пользователям за фидбэк и предложения

---

**Приятного использования и удачных покупок!** 🎲✨