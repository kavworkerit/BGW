# 🪟 Установка и запуск BGW в Windows

## 📋 Системные требования

- **Windows 10/11** (64-bit)
- **Docker Desktop** (последняя версия)
- **WSL2** (Windows Subsystem for Linux 2)
- **минимум 4GB RAM** (рекомендовано 8GB+)
- **10GB+ свободного места** на диске

## 🐳 Установка Docker Desktop

### 1. Активация WSL2
```powershell
# В PowerShell с правами администратора
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Перезагрузка Windows
```

### 2. Установка Docker Desktop
1. Скачать [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Запустить установщик с правами администратора
3. Следовать инструкциям установщика
4. Перезагрузить компьютер после установки
5. Запустить Docker Desktop

### 3. Настройка WSL2
```powershell
# Установка WSL2
wsl --install

# Установка дистрибутива Ubuntu
wsl --install Ubuntu

# Перезагрузка после установки
```

### 4. Проверка Docker
```powershell
# Проверить версию Docker
docker --version

# Проверить версию Docker Compose
docker-compose --version

# Проверить работу (должен показать hello-world)
docker run hello-world
```

## 🚀 Быстрый запуск BGW

### 1. Клонирование репозитория
```powershell
# Создаем папку для проектов
mkdir C:\Projects
cd C:\Projects

# Клонируем репозиторий (замените URL на реальный)
git clone https://github.com/kavworkerit/BGW.git
cd bgw
```

### 2. Первичная настройка
```powershell
# Копируем файл окружения
copy .env.example .env

# Открываем для редактирования (рекомендуется VS Code)
code .env
```

**Настройки в .env (минимальные):**
```bash
# Часовой пояс
TZ=Europe/Moscow

# База данных (оставить как есть)
DATABASE_URL=postgresql+psycopg2://app:app@postgres:5432/app

# Redis (оставить как есть)
REDIS_URL=redis://redis:6379/0

# MinIO (оставить как есть)
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin

# Опционально: Ollama (если установлен локально)
OLLAMA_URL=http://host.docker.internal:11434

# Опционально: Telegram (если нужен)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Запуск системы
```powershell
# Запуск всех сервисов в фоновом режиме
docker-compose up -d

# Просмотр логов запуска
docker-compose logs -f
```

### 4. Проверка запуска
```powershell
# Статус всех контейнеров
docker-compose ps

# Проверить что все контейнеры работают
# Должны быть в статусе "Up" или "running"
```

## 🔗 Доступ к системе

После успешного запуска система доступна по адресам:

| Сервис | URL | Логин/Пароль | Примечание |
|--------|-----|-------------|-----------|
| **Основной интерфейс** | http://localhost | - | Главная система |
| **API документация** | http://localhost:8000/docs | - | Swagger UI |
| **Grafana дашборды** | http://localhost:3001 | admin/admin | Мониторинг |
| **MinIO консоль** | http://localhost:9001 | minioadmin/minioadmin | Хранилище файлов |
| **Prometheus** | http://localhost:9090 | - | Метрики |

## 🔧 Первоначальная настройка BGW

### 1. Настройка агентов
1. Открыть http://localhost в браузере
2. Перейти в раздел **"Агенты"**
3. Включить нужные магазины:
   - ✅ Hobby Games
   - ✅ Лавка Игр
   - ✅ Nastol.io
   - ✅ И другие по желанию
4. Проверить расписание (каждые 2-4 часа)

### 2. Добавление игр
1. Перейти в **"Игры"**
2. Нажать **"Добавить игру"**
3. Примеры игр для теста:
   - "Громкое дело"
   - "Dune: Империум"
   - "Колонизаторы Марса"

### 3. Настройка уведомлений
1. Перейти в **"Правила"**
2. Создать новое правило:
   - **Название**: "Скидки > 20%"
   - **Условие**: `discount_pct >= 20`
   - **Канал**: Web Push
3. Подключить Web Push в браузере (значок колокольчика)

## 🐛 Troubleshooting в Windows

### Проблема: Docker не запускается
**Решение:**
1. Убедиться что WSL2 включен: `wsl --list`
2. Проверить Docker Desktop запущен
3. Перезапустить Docker Desktop
4. Перезагрузить компьютер

### Проблема: Контейнеры не запускаются
```powershell
# Проверить логи
docker-compose logs api
docker-compose logs postgres

# Остановить все контейнеры
docker-compose down

# Очистить Docker систему
docker system prune -a

# Запустить снова
docker-compose up -d
```

### Проблема: Ошибки с портами
**Если порты 80, 8000, 3001 заняты:**
```powershell
# Найти процесс использующий порт
netstat -ano | findstr ":80"

# Изменить порты в docker-compose.yml
ports:
  - "8080:80"  # изменить с 80:80
```

### Проблема: Медленная работа в WSL2
**Оптимизация производительности:**
1. Создать файл `.wslconfig`:
```ini
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true
```

2. Перезапустить WSL:
```powershell
wsl --shutdown
```

## 🔄 Работа с системой

### Полезные команды
```powershell
# Просмотр логов конкретного сервиса
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f frontend

# Перезапуск конкретного сервиса
docker-compose restart api
docker-compose restart worker

# Вход в контейнер для отладки
docker-compose exec api bash
docker-compose exec postgres psql -U app -d app

# Остановка всех сервисов
docker-compose down

# Остановка с удалением данных
docker-compose down -v
```

### Бэкап и восстановление
```powershell
# Создать бэкап БД
docker-compose exec postgres pg_dump -U app app > backup.sql

# Восстановить бэкап
docker-compose exec -T postgres psql -U app app < backup.sql

# Бэкап всех данных (через UI)
# Настройки → Экспорт → Скачать ZIP
```

## 📱 Мобильный доступ

### Web Push уведомления
1. Открыть http://localhost в мобильном браузере
2. Разрешить уведомления при первом посещении
3. Добавить сайт на главный экран (PWA)

### Telegram бот (опционально)
1. Создать бота: @BotFather в Telegram
2. Получить токен бота
3. Получить chat ID: @userinfobot
4. Добавить в `.env`:
```bash
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
TELEGRAM_CHAT_ID=123456789
```
5. Перезапустить контейнеры: `docker-compose restart api`

## ⚙️ Продвинутая настройка

### Настройка Ollama для AI функций
```powershell
# Запуск Ollama в Docker (опционально)
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Установка моделей
docker exec -it ollama ollama pull llama2
docker exec -it ollama ollama pull mistral
```

### Настройка HTTPS (для production)
1. Получить SSL сертификат (Let's Encrypt)
2. Обновить `deploy/nginx.conf`
3. Изменить порты в `docker-compose.yml`
4. Использовать `docker-compose.prod.yml`

## 📞 Поддержка

### Логи и отладка
```powershell
# Все логи
docker-compose logs --tail=100

# Логи за последние 5 минут
docker-compose logs --since=5m

# Сохранить логи в файл
docker-compose logs > bgw-logs.txt
```

### Мониторинг производительности
- **Grafana**: http://localhost:3001
- **System Overview**: загрузка CPU/RAM
- **Agent Performance**: успех парсинга
- **Business Metrics**: количество событий

### Частые вопросы

**Q: Система работает медленно?**
A: Проверьте:
- Загрузку CPU/RAM в Grafana
- Свободное место на диске
- Сетевое подключение

**Q: Нет уведомлений в браузере?**
A: Убедитесь что:
- Браузер разрешен для уведомлений
- Сайт добавлен в разрешенные
- Правило уведомлений активно

**Q: Агенты не собирают данные?**
A: Проверьте:
- Статус агентов в UI
- Логи worker: `docker-compose logs -f worker`
- Доступность сайтов магазинов

---

## 🎉 Поздравляем!

BGW полностью готов к использованию в Windows. Система будет автоматически:
- 🤖 Собирать данные с 10+ магазинов
- 📊 Отслеживать изменения цен
- 🔔 Отправлять уведомления о скидках
- 📈 Строить аналитику и графики

**Следующие шаги:**
1. Настройте агенты под свои интересы
2. Добавьте любимые игры в watchlist
3. Создайте правила для уведомлений
4. Наслаждайтесь мониторингом лучших цен!

Для дополненной информации см. [основную документацию](../README.md).