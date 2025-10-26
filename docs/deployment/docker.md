# Docker развертывание

## Обзор

BGW использует Docker Compose для оркестрации всех сервисов. Это обеспечивает изолированную среду, воспроизводимость и простоту развертывания.

## Архитектура контейнеров

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │     │   Backend   │     │    Nginx    │
│   (React)   │────▶│  (FastAPI)  │────▶│ (Reverse    │
│   :3000     │     │   :8000     │     │   Proxy)    │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                   ┌───────┼────────┐
                   │       │        │
            ┌─────────────┐ ┌─────────────┐
            │   Worker    │ │    Beat     │
            │  (Celery)   │ │ (Scheduler) │
            └─────────────┘ └─────────────┘
                   │       │
            ┌─────────────────────────────┐
            │       Data Layer           │
            │ ┌─────┐ ┌─────┐ ┌─────┐   │
            │ │PG+TS│ │Redis│ │MinIO│   │
            │ └─────┘ └─────┘ └─────┘   │
            └─────────────────────────────┘
```

## docker-compose.yml

Основной файл конфигурации:

```yaml
version: '3.8'

services:
  # Backend API
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
      minio:
        condition: service_healthy
    volumes:
      - ./backend:/app  # Для hot reload в разработке
      - ./agents:/app/agents  # Пользовательские агенты
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Celery Worker
  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery_app worker -l INFO --concurrency=2
    env_file: .env
    depends_on:
      api:
        condition: service_healthy
      redis:
        condition: service_started
      postgres:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - ./agents:/app/agents
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "celery", "inspect", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Celery Beat Scheduler
  beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery_app beat -l INFO --schedule=/tmp/celerybeat-schedule
    env_file: .env
    depends_on:
      worker:
        condition: service_healthy
      redis:
        condition: service_started
    volumes:
      - ./backend:/app
      - ./agents:/app/agents
      - celerybeat_data:/tmp  # Сохранение состояния планировщика
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "celery", "inspect", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - REACT_APP_API_URL=http://localhost/api
    env_file: .env
    depends_on:
      api:
        condition: service_healthy
    volumes:
      - ./frontend:/app  # Для hot reload
      - /app/node_modules  # Изолируем node_modules
    restart: unless-stopped

  # Nginx Reverse Proxy
  nginx:
    image: nginx:stable-alpine
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./deploy/nginx/site.conf:/etc/nginx/conf.d/default.conf:ro
      - static_files:/var/www/static  # Статические файлы бэкенда
      - frontend_build:/var/www/html  # Сборка фронтенда
    ports:
      - "80:80"
      - "443:443"  # Для HTTPS
    depends_on:
      frontend:
        condition: service_started
      api:
        condition: service_healthy
    restart: unless-stopped

  # PostgreSQL + TimescaleDB
  postgres:
    image: timescale/timescaledb:latest-pg15
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-app}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-app}
      POSTGRES_DB: ${POSTGRES_DB:-app}
      POSTGRES_INITDB_ARGS: "--encoding=UTF-8 --lc-collate=C --lc-ctype=C"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./deploy/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      - ./deploy/postgres/timescaledb.conf:/etc/postgresql/postgresql.conf:ro
    ports:
      - "5432:5432"  # Для локального доступа
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app} -d ${POSTGRES_DB:-app}"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: >
      postgres
      -c config_file=/etc/postgresql/postgresql.conf
      -c shared_preload_libraries=timescaledb
      -c max_connections=200
      -c shared_buffers=256MB
      -c effective_cache_size=1GB

  # Redis
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redisdata:/data
      - ./deploy/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    ports:
      - "6379:6379"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  # MinIO S3 Storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${S3_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${S3_SECRET_KEY:-minioadmin}
      MINIO_BROWSER_REDIRECT_URL: http://localhost:9001
    volumes:
      - minio:/data
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # Prometheus Monitoring
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/web/libs/ui'
      - '--web.console.templates=/usr/share/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    volumes:
      - ./deploy/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./deploy/bgw_rules.yml:/etc/prometheus/bgw_rules.yml:ro
      - prometheus_data:/prometheus
    restart: unless-stopped
    depends_on:
      api:
        condition: service_healthy

  # Grafana Dashboards
  grafana:
    image: grafana/grafana:latest
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_INSTALL_PLUGINS: "grafana-piechart-panel,grafana-worldmap-panel"
      GF_SECURITY_ALLOW_EMBEDDING: "true"
      GF_AUTH_ANONYMOUS_ENABLED: "false"
      GF_SERVER_ROOT_URL: "http://localhost:3001/"
    ports:
      - "3001:3000"
    volumes:
      - ./deploy/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./deploy/grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafana_data:/var/lib/grafana
    restart: unless-stopped
    depends_on:
      prometheus:
        condition: service_started

  # Daily Backup Job
  backup:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: >
      sh -c "
      echo 'Waiting for backup time...' &&
      while true; do
        current_hour=$(date +%H) &&
        if [ $current_hour -eq 3 ]; then
          echo 'Starting daily backup...' &&
          python -m app.jobs.backup_daily &&
          echo 'Backup completed, waiting until next day...' &&
          sleep 86400;
        else
          sleep 3600;
        fi;
      done
      "
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      minio:
        condition: service_healthy
    volumes:
      - ./backups:/app/backups
      - ./backend:/app
    restart: "no"  # Запускается вручную или по крону хоста
    profiles:
      - backup  # Включается только при необходимости

# Внешние volumes для сохранения данных
volumes:
  pgdata:
    driver: local
  redisdata:
    driver: local
  minio:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
  celerybeat_data:
    driver: local
  static_files:
    driver: local
  frontend_build:
    driver: local

# Сеть для всех сервисов
networks:
  default:
    name: bgw-network
    driver: bridge
```

## Dockerfile конфигурации

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Создание директорий
RUN mkdir -p /app/logs /app/uploads /app/agents

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Пользователь (без root)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Запуск
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine AS builder

# Рабочая директория
WORKDIR /app

# Копирование package files
COPY package*.json ./

# Установка зависимостей
RUN npm ci --only=production && npm cache clean --force

# Копирование исходного кода
COPY . .

# Аргументы для сборки
ARG REACT_APP_API_URL=http://localhost/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Сборка
RUN npm run build

# Production stage
FROM nginx:stable-alpine

# Копирование сборки
COPY --from=builder /app/build /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## Конфигурация Nginx

### Основной конфигурация

```nginx
# deploy/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Логирование
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # Оптимизации
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 10M;

    # Gzip сжатие
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;

    # Include site configs
    include /etc/nginx/conf.d/*.conf;
}
```

### Конфигурация сайта

```nginx
# deploy/nginx/site.conf
upstream api_backend {
    server api:8000;
    keepalive 32;
}

# Rate limiting для API
limit_req_status 429;

server {
    listen 80;
    server_name localhost;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Frontend
    location / {
        root /var/www/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;

        # Кэширование статических файлов
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API
    location /api/ {
        limit_req zone=api burst=20 nodelay;

        proxy_pass http://api_backend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API_docs
    location /docs {
        proxy_pass http://api_backend/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health endpoint
    location /healthz {
        access_log off;
        proxy_pass http://api_backend/healthz;
    }

    # Login endpoint (stricter rate limiting)
    location /api/auth/login {
        limit_req zone=login burst=5 nodelay;

        proxy_pass http://api_backend/auth/login;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Error pages
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

## Развертывание

### Первоначальный запуск

```bash
# Клонирование репозитория
git clone <repository-url>
cd BGW

# Настройка окружения
cp .env.example .env
nano .env  # Редактирование конфигурации

# Запуск всех сервисов
docker-compose up -d

# Проверка статуса
docker-compose ps

# Просмотр логов
docker-compose logs -f

# Инициализация базы данных
docker-compose exec api alembic upgrade head

# Создание администратора (если нужно)
docker-compose exec api python -m app.scripts.create_admin
```

### Production развертывание

```bash
# Production конфигурация
cp docker-compose.yml docker-compose.prod.yml

# Изменения для production:
# - Убрать volume монтирования для разработки
# - Добавить SSL терминирование
# - Настроить бэкапы
# - Включить мониторинг

# Запуск в production режиме
docker-compose -f docker-compose.prod.yml up -d

# Масштабирование воркеров
docker-compose -f docker-compose.prod.yml up -d --scale worker=3
```

### SSL/HTTPS конфигурация

```nginx
# deploy/nginx/ssl.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Остальная конфигурация...
}
```

## Мониторинг и обслуживание

### Health checks

```bash
# Проверка здоровья всех сервисов
docker-compose exec api curl -f http://localhost:8000/healthz
docker-compose exec worker celery inspect ping
docker-compose exec redis redis-cli ping
docker-compose exec postgres pg_isready -U app

# Статус контейнеров
docker-compose ps
docker-compose top
```

### Логирование

```bash
# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker-compose logs -f api
docker-compose logs -f worker

# Логи за последние 100 строк
docker-compose logs --tail=100

# Логи с временными метками
docker-compose logs -t
```

### Обновление

```bash
# Pull изменений
git pull

# Пересборка образов
docker-compose build --no-cache

# Перезапуск с миграциями
docker-compose up -d
docker-compose exec api alembic upgrade head

# Очистка старых образов
docker image prune -f
```

### Резервное копирование

```bash
# Бэкап базы данных
docker-compose exec postgres pg_dump -U app app > backup_$(date +%Y%m%d).sql

# Бэкап volumes
docker run --rm -v bgw_pgdata:/data -v $(pwd):/backup alpine tar czf /backup/pgdata_backup.tar.gz -C /data .

# Восстановление БД
docker-compose exec -T postgres psql -U app app < backup_20240101.sql
```

## Оптимизация производительности

### Resource limits

```yaml
# docker-compose.prod.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  worker:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  postgres:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
```

### Кэширование

```yaml
# Redis кэширование
redis:
  image: redis:7-alpine
  command: >
    redis-server
    --maxmemory 1gb
    --maxmemory-policy allkeys-lru
    --save 900 1
    --save 300 10
    --save 60 10000
```

## Troubleshooting

### Частые проблемы

1. **Проблема**: Контейнеры не стартуют
   **Решение**: Проверить `.env` файл, свободные порты, права доступа

2. **Проблема**: База данных не доступна
   **Решение**: Проверить health check, логи postgres, правильность паролей

3. **Проблема**: Worker не обрабатывает задачи
   **Решение**: Проверить соединение с Redis, логи Celery, очереди

4. **Проблема**: Нет доступа к UI
   **Решение**: Проверить Nginx конфигурацию, порты, бэкенд API

### Диагностика

```bash
# Информация о контейнерах
docker-compose config
docker network ls
docker volume ls

# Внутрь контейнера
docker-compose exec api bash
docker-compose exec postgres psql -U app -d app

# Мониторинг ресурсов
docker stats
docker-compose top
```

Эта документация обеспечивает полное понимание Docker развертывания и эксплуатации системы BGW.