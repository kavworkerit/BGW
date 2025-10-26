#!/usr/bin/env pwsh

# Скрипт для автоматического развертывания проекта Board Games Monitor
# Требования: PowerShell 7+, Docker, Docker Compose

param(
    [string]$InstallDir = "C:\BoardGamesMonitor",
    [string]$GitRepo = "https://github.com/your-username/board-games-monitor.git",
    [switch]$SkipDockerCheck = $false,
    [switch]$SkipEnvFile = $false,
    [switch]$DevMode = $false
)

Write-Host "🎲 Board Games Monitor - Скрипт развертывания" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Проверка прав администратора
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    Write-Host "⚠️  Для корректной работы Docker требуются права администратора" -ForegroundColor Yellow
    Write-Host "   Запустите PowerShell от имени администратора" -ForegroundColor Yellow
    $continue = Read-Host "Продолжить без прав администратора? (y/N)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Проверка Docker
if (-not $SkipDockerCheck) {
    Write-Host "🔍 Проверка Docker..." -ForegroundColor Green

    try {
        docker version | Out-Null
        if ($LASTEXITCODE -ne 0) { throw }
        Write-Host "✅ Docker найден" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker не найден. Пожалуйста, установите Docker Desktop" -ForegroundColor Red
        Write-Host "   Скачайте: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
        exit 1
    }

    try {
        docker-compose version | Out-Null
        if ($LASTEXITCODE -ne 0) { throw }
        Write-Host "✅ Docker Compose найден" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Docker Compose не найден" -ForegroundColor Red
        exit 1
    }
}

# Создание директории установки
Write-Host "📁 Создание директории установки: $InstallDir" -ForegroundColor Green
if (Test-Path $InstallDir) {
    Write-Host "⚠️  Директория уже существует" -ForegroundColor Yellow
    $overwrite = Read-Host "Перезаписать существующие файлы? (y/N)"
    if ($overwrite -eq "y") {
        Remove-Item -Path "$InstallDir\*" -Recurse -Force -ErrorAction SilentlyContinue
    }
    else {
        Write-Host "❌ Отмена установки" -ForegroundColor Red
        exit 1
    }
}
else {
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
}

Set-Location $InstallDir

# Клонирование репозитория
Write-Host "📥 Клонирование репозитория..." -ForegroundColor Green
try {
    git clone $GitRepo .
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "✅ Репозиторий склонирован" -ForegroundColor Green
}
catch {
    Write-Host "❌ Не удалось клонировать репозиторий" -ForegroundColor Red
    Write-Host "   Проверьте подключение к интернету и права доступа" -ForegroundColor Yellow
    exit 1
}

# Создание .env файла
if (-not $SkipEnvFile) {
    Write-Host "⚙️  Создание конфигурационного файла .env..." -ForegroundColor Green

    $envFile = @"
# Часовой пояс
TZ=Europe/Moscow

# База данных
DATABASE_URL=postgresql+psycopg2://app:app@postgres:5432/app

# Redis
REDIS_URL=redis://redis:6379/0

# MinIO S3 хранилище
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=raw
S3_SECURE=false

# Ollama (опционально)
# OLLAMA_URL=http://host.docker.internal:11434

# Безопасность
SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=http://localhost,http://localhost:3000

# Telegram (опционально)
# TELEGRAM_BOT_TOKEN=your_bot_token_here
# TELEGRAM_CHAT_ID=your_chat_id_here

# Web Push
VAPID_PUBLIC_KEY=your_vapid_public_key
VAPID_PRIVATE_KEY=your_vapid_private_key
VAPID_EMAIL=your_email@example.com

# Ограничения
MAX_DAILY_PAGES=1000
DEFAULT_RPS=0.3
DEFAULT_BURST=1

# Логирование
LOG_LEVEL=INFO
"@

    # Генерация секретного ключа
    try {
        $secretKey = -join ((1..32) | ForEach-Object { '{0:x}' -f (Get-Random -Maximum 255) })
        $envFile = $envFile -replace '\$\(openssl rand -hex 32\)', $secretKey
    }
    catch {
        $envFile = $envFile -replace '\$\(openssl rand -hex 32\)', 'change-this-secret-key-in-production'
    }

    # Генерация VAPID ключей
    $envFile = $envFile -replace 'your_vapid_public_key', 'your-vapid-public-key-here'
    $envFile = $envFile -replace 'your_vapid_private_key', 'your-vapid-private-key-here'

    Set-Content -Path ".env" -Value $envFile -Encoding UTF8
    Write-Host "✅ Файл .env создан" -ForegroundColor Green
    Write-Host "   При необходимости отредактируйте его для настройки Telegram и других параметров" -ForegroundColor Yellow
}

# Создание директорий
Write-Host "📁 Создание необходимых директорий..." -ForegroundColor Green
$directories = @("backups", "agents", "logs")
foreach ($dir in $directories) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
}

# Сборка и запуск Docker контейнеров
Write-Host "🐳 Сборка Docker образов..." -ForegroundColor Green
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка сборки Docker образов" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Docker образы собраны" -ForegroundColor Green

# Запуск контейнеров
Write-Host "🚀 Запуск контейнеров..." -ForegroundColor Green
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка запуска контейнеров" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Контейнеры запущены" -ForegroundColor Green

# Ожидание запуска сервисов
Write-Host "⏳ Ожидание запуска сервисов..." -ForegroundColor Green
Start-Sleep -Seconds 30

# Проверка состояния
Write-Host "🔍 Проверка состояния сервисов..." -ForegroundColor Green
docker-compose ps

# Миграция базы данных
Write-Host "🗄️  Выполнение миграций базы данных..." -ForegroundColor Green
docker-compose exec -T api alembic upgrade head
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Ошибка миграции базы данных. Проверьте логи" -ForegroundColor Yellow
}
else {
    Write-Host "✅ Миграции выполнены" -ForegroundColor Green
}

# Создание скрипта для управления
Write-Host "📜 Создание скрипта управления..." -ForegroundColor Green
$manageScript = @"
# Скрипт управления Board Games Monitor
# Использование: .\manage.ps1 [start|stop|restart|logs|status|update|backup]

param(
    [Parameter(Position=0)]
    [ValidateSet("start", "stop", "restart", "logs", "status", "update", "backup")]
    [string]`$Action = "status"
)

Write-Host "🎲 Board Games Monitor Manager" -ForegroundColor Cyan

switch (`$Action) {
    "start" {
        Write-Host "🚀 Запуск сервисов..." -ForegroundColor Green
        docker-compose up -d
    }

    "stop" {
        Write-Host "🛑 Остановка сервисов..." -ForegroundColor Yellow
        docker-compose down
    }

    "restart" {
        Write-Host "🔄 Перезапуск сервисов..." -ForegroundColor Green
        docker-compose restart
    }

    "logs" {
        Write-Host "📋 Логи сервисов..." -ForegroundColor Blue
        docker-compose logs -f
    }

    "status" {
        Write-Host "📊 Статус сервисов:" -ForegroundColor Green
        docker-compose ps
    }

    "update" {
        Write-Host "🔄 Обновление..." -ForegroundColor Green
        git pull
        docker-compose build
        docker-compose up -d
    }

    "backup" {
        Write-Host "💾 Создание бэкапа..." -ForegroundColor Green
        `$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
        `$backupFile = "backups/backup_`$timestamp.zip"

        # Создание бэкапа базы данных
        docker-compose exec -T postgres pg_dump -U app app > "backups/db_`$timestamp.sql"

        # Архивация
        Compress-Archive -Path "backups/db_`$timestamp.sql" -DestinationPath `$backupFile
        Remove-Item "backups/db_`$timestamp.sql"

        Write-Host "✅ Бэкап создан: `$backupFile" -ForegroundColor Green
    }
}

Write-Host "✅ Готово!" -ForegroundColor Green
"@

Set-Content -Path "manage.ps1" -Value $manageScript -Encoding UTF8

# Вывод информации
Write-Host "" -ForegroundColor White
Write-Host "🎉 Установка завершена!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host "📱 Веб-интерфейс доступен по адресу: http://localhost" -ForegroundColor Cyan
Write-Host "🔧 API доступен по адресу: http://localhost/api" -ForegroundColor Cyan
Write-Host "📊 МинIO консоль: http://localhost:9001 (minioadmin/minioadmin)" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White
Write-Host "📜 Управление сервисами:" -ForegroundColor Yellow
Write-Host "   .\manage.ps1 start    - Запустить сервисы" -ForegroundColor White
Write-Host "   .\manage.ps1 stop     - Остановить сервисы" -ForegroundColor White
Write-Host "   .\manage.ps1 restart  - Перезапустить сервисы" -ForegroundColor White
Write-Host "   .\manage.ps1 logs     - Просмотреть логи" -ForegroundColor White
Write-Host "   .\manage.ps1 status   - Показать статус" -ForegroundColor White
Write-Host "   .\manage.ps1 update   - Обновить" -ForegroundColor White
Write-Host "   .\manage.ps1 backup   - Создать бэкап" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "📖 Документация: https://github.com/your-username/board-games-monitor" -ForegroundColor Cyan
Write-Host "" -ForegroundColor White

if ($DevMode) {
    Write-Host "🛠️  Режим разработки:" -ForegroundColor Yellow
    Write-Host "   API: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   Frontend: http://localhost:3000" -ForegroundColor White
}

Write-Host "✨ Приятного использования!" -ForegroundColor Green