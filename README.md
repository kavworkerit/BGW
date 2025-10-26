# 🎲 Мониторинг настольных игр

Система для мониторинга релизов, предзаказов и скидок настольных игр из различных интернет-магазинов и источников.

## ✨ Возможности

- 🎯 **Мониторинг источников** - отслеживание до 100 источников (магазины, публикации, каталоги)
- 📊 **История цен** - хранение и анализ цен на игры за 2 года
- 🔔 **Уведомления** - Web-Push и Telegram оповещения о событиях
- 🤖 **Агентная платформа** - гибкая система парсинга с поддержкой разных типов источников
- 📈 **Аналитика** - графики цен и статистика
- 🐳 **Docker** - простое развертывание в один клик

## 🏗️ Архитектура

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React с Ant Design
- **База данных**: PostgreSQL 15 + TimescaleDB
- **Брокер**: Redis + Celery
- **Хранилище**: MinIO (S3-совместимое)
- **Прокси**: Nginx

## 🚀 Быстрый старт

### Автоматическая установка

#### Windows (PowerShell)

```powershell
# Скачайте и запустите скрипт
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-username/board-games-monitor/main/deploy.ps1" -OutFile "deploy.ps1"
.\deploy.ps1

# Или с параметрами
.\deploy.ps1 -InstallDir "C:\BoardGamesMonitor" -DevMode
```

#### Linux/macOS

```bash
# Скачайте и запустите скрипт
curl -fsSL https://raw.githubusercontent.com/your-username/board-games-monitor/main/deploy.sh -o deploy.sh
chmod +x deploy.sh
./deploy.sh

# Или с параметрами
./deploy.sh $HOME/board-games-monitor https://github.com/your-username/board-games-monitor.git
```

### Ручная установка

1. **Клонирование репозитория**
   ```bash
   git clone https://github.com/your-username/board-games-monitor.git
   cd board-games-monitor
   ```

2. **Настройка окружения**
   ```bash
   cp .env.example .env
   # Отредактируйте .env файл по вашему усмотрению
   ```

3. **Запуск с Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Миграция базы данных**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

## 📱 Доступ к сервисам

После установки сервисы будут доступны по следующим адресам:

- 🌐 **Веб-интерфейс**: http://localhost
- 🔧 **API документация**: http://localhost/api/docs
- 📊 **MinIO консоль**: http://localhost:9001 (minioadmin/minioadmin)
- 🗄️ **PostgreSQL**: localhost:5432
- 📨 **Redis**: localhost:6379

## 🎮 Использование

### 1. Добавление игр в watchlist

Перейдите в раздел **"Игры"** и добавьте игры, которые вы хотите отслеживать:

- Основное название игры
- Синонимы (включая английские варианты)
- BGG ID (опционально)
- Издатель и теги для удобства фильтрации

### 2. Настройка агентов

В разделе **"Агенты"** вы можете:

- Создать нового агента для мониторинга источника
- Импортировать готового агента из ZIP файла
- Настроить расписание и ограничения
- Просмотреть логи работы

### 3. Создание правил уведомлений

В разделе **"Правила"** создайте условия для получения уведомлений:

**Примеры правил:**

- *Искомая игра + предзаказ/релиз*
  ```
  Логика: ИЛИ
  Условия:
  - Игра: "Громкое дело"
  - Заголовок содержит: "предзаказ" ИЛИ "в продаже"
  ```

- *Скидка 20%+ в определенных магазинах*
  ```
  Логика: И
  Условия:
  - Скидка >= 20%
  - Магазин: "Лавка Игр" ИЛИ "Hobby Games"
  ```

### 4. Мониторинг событий

В разделе **"События"** отслеживайте все события:

- Фильтрация по играм, магазинам, типам событий
- Просмотр истории цен
- Переходы на исходные страницы

## 🤖 Агентная платформа

### Создание собственного агента

1. **Создайте файл агента**:
   ```python
   from app.agents.base import HTMLAgent, Fetched, ListingEventDraft

   class MyStoreAgent(HTMLAgent):
       async def parse(self, fetched: Fetched):
           soup = BeautifulSoup(fetched.body, 'html.parser')
           # Логика парсинга
           yield ListingEventDraft(title=title, price=price)
   ```

2. **Создайте манифест**:
   ```json
   {
     "id": "mystore_agent",
     "name": "My Store Agent",
     "type": "html",
     "entrypoint": "agent.py",
     "schedule": {"cron": "0 */2 * * *"},
     "rate_limit": {"rps": 0.3, "daily_pages_cap": 50},
     "config": {
       "start_urls": ["https://mystore.com/catalog"],
       "selectors": {
         "item": ".product-card",
         "title": ".product-title",
         "price": ".price"
       }
     }
   }
   ```

3. **Упакуйте в ZIP** и импортируйте через интерфейс.

## 🔧 Конфигурация

### Переменные окружения (.env)

```bash
# Основные настройки
TZ=Europe/Moscow
SECRET_KEY=your-secret-key

# База данных
DATABASE_URL=postgresql+psycopg2://app:app@postgres:5432/app

# Redis
REDIS_URL=redis://redis:6379/0

# Telegram (опционально)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Ollama для LLM (опционально)
OLLAMA_URL=http://host.docker.internal:11434

# Ограничения
MAX_DAILY_PAGES=1000
DEFAULT_RPS=0.3
```

### Управление сервисами

```bash
# Запуск
docker-compose up -d

# Остановка
docker-compose down

# Просмотр логов
docker-compose logs -f

# Обновление
docker-compose pull && docker-compose up -d

# Создание бэкапа
docker-compose exec postgres pg_dump -U app app > backup.sql
```

## 📊 Стартовые источники

Система включает преднастроенных агентов для:

- 🎯 **Hobby Games** - coming-soon и catalog-new
- 🎯 **Лавка Игр** - магазин и проекты
- 🎯 **Nastol.io** - публикации и конкретные статьи
- 🎯 **Evrikus** - каталог
- 🎯 **CrowdGames** - коллекция игр
- 🎯 **Gaga.ru** - каталог
- 🎯 **Zvezda.org.ru** - настольные игры
- 🎯 **ChooChooGames** - магазин

## 🔔 Уведомления

### Web Push

Настройте в интерфейсе:
1. Сгенерируйте VAPID ключи
2. Подпишитесь в браузере на уведомления
3. Настройте тихие часы при необходимости

### Telegram

1. Создайте бота через @BotFather
2. Получите токен бота
3. Найдите свой Chat ID через @userinfobot
4. Введите данные в настройках

## 📈 Мониторинг и аналитика

- **Дашборд** - обзор состояния системы
- **Графики цен** - история цен по играм и магазинам
- **Статистика агентов** - успешность выполнения, ошибки, использование лимитов
- **Метрики** - Prometheus метрики для мониторинга

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
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Запуск воркеров
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

- 📖 [Документация](https://github.com/your-username/board-games-monitor/wiki)
- 🐛 [Баг-трекер](https://github.com/your-username/board-games-monitor/issues)
- 💬 [Обсуждения](https://github.com/your-username/board-games-monitor/discussions)

## 🙏 Благодарности

- Сообществу BoardGameGeek за данные об играх
- Разработчикам библиотек, которые делают этот проект возможным
- Пользователям за фидбэк и предложения

---

**Приятного использования и удачных покупок!** 🎲✨