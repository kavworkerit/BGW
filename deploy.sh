#!/bin/bash

# Скрипт для автоматического развертывания проекта Board Games Monitor
# Требования: Bash 4+, Docker, Docker Compose, Git

set -e

# Параметры
INSTALL_DIR="${1:-$HOME/board-games-monitor}"
GIT_REPO="${2:-https://github.com/your-username/board-games-monitor.git}"
SKIP_DOCKER_CHECK="${3:-false}"
SKIP_ENV_FILE="${4:-false}"
DEV_MODE="${5:-false}"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функции для вывода
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${CYAN}🎲 Board Games Monitor - Скрипт развертывания${NC}"
    echo -e "${CYAN}===========================================${NC}"
}

# Проверка зависимостей
check_dependencies() {
    if [ "$SKIP_DOCKER_CHECK" = "false" ]; then
        print_info "Проверка Docker..."

        if ! command -v docker &> /dev/null; then
            print_error "Docker не найден. Пожалуйста, установите Docker"
            print_info "   Ubuntu/Debian: sudo apt install docker.io docker-compose"
            print_info "   CentOS/RHEL: sudo yum install docker docker-compose"
            print_info "   macOS: Скачайте с https://www.docker.com/products/docker-desktop"
            exit 1
        fi
        print_success "Docker найден"

        if ! command -v docker-compose &> /dev/null; then
            print_error "Docker Compose не найден"
            exit 1
        fi
        print_success "Docker Compose найден"
    fi

    if ! command -v git &> /dev/null; then
        print_error "Git не найден. Пожалуйста, установите Git"
        print_info "   Ubuntu/Debian: sudo apt install git"
        print_info "   CentOS/RHEL: sudo yum install git"
        exit 1
    fi
    print_success "Git найден"
}

# Создание директории установки
create_install_dir() {
    print_info "Создание директории установки: $INSTALL_DIR"

    if [ -d "$INSTALL_DIR" ]; then
        print_warning "Директория уже существует"
        read -p "Перезаписать существующие файлы? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$INSTALL_DIR"/*
        else
            print_error "Отмена установки"
            exit 1
        fi
    else
        mkdir -p "$INSTALL_DIR"
    fi

    cd "$INSTALL_DIR"
}

# Клонирование репозитория
clone_repository() {
    print_info "Клонирование репозитория..."

    if ! git clone "$GIT_REPO" . 2>/dev/null; then
        print_error "Не удалось клонировать репозиторий"
        print_info "   Проверьте подключение к интернету и права доступа"
        exit 1
    fi

    print_success "Репозиторий склонирован"
}

# Создание .env файла
create_env_file() {
    if [ "$SKIP_ENV_FILE" = "false" ]; then
        print_info "Создание конфигурационного файла .env..."

        # Генерация секретного ключа
        SECRET_KEY=$(openssl rand -hex 32 2>/dev/null || echo "change-this-secret-key-in-production-$(date +%s)")

        cat > .env << EOF
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
SECRET_KEY=$SECRET_KEY
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
EOF

        print_success "Файл .env создан"
        print_warning "   При необходимости отредактируйте его для настройки Telegram и других параметров"
    fi
}

# Создание директорий
create_directories() {
    print_info "Создание необходимых директорий..."

    for dir in backups agents logs; do
        mkdir -p "$dir"
    done
}

# Сборка и запуск контейнеров
build_and_start() {
    print_info "Сборка Docker образов..."

    if ! docker-compose build; then
        print_error "Ошибка сборки Docker образов"
        exit 1
    fi

    print_success "Docker образы собраны"

    print_info "Запуск контейнеров..."

    if ! docker-compose up -d; then
        print_error "Ошибка запуска контейнеров"
        exit 1
    fi

    print_success "Контейнеры запущены"
}

# Ожидание запуска сервисов
wait_for_services() {
    print_info "Ожидание запуска сервисов..."
    sleep 30

    print_info "Проверка состояния сервисов..."
    docker-compose ps
}

# Миграция базы данных
migrate_database() {
    print_info "Выполнение миграций базы данных..."

    # Ждем запуска API
    for i in {1..30}; do
        if docker-compose exec -T api python -c "import app.core.database; print('OK')" 2>/dev/null; then
            break
        fi
        sleep 2
    done

    if docker-compose exec -T api alembic upgrade head 2>/dev/null; then
        print_success "Миграции выполнены"
    else
        print_warning "Ошибка миграции базы данных. Проверьте логи"
    fi
}

# Создание скрипта управления
create_manage_script() {
    print_info "Создание скрипта управления..."

    cat > manage.sh << 'EOF'
#!/bin/bash

# Скрипт управления Board Games Monitor
# Использование: ./manage.sh [start|stop|restart|logs|status|update|backup]

ACTION="${1:-status}"

print_info() {
    echo -e "\033[0;34mℹ️  $1\033[0m"
}

print_success() {
    echo -e "\033[0;32m✅ $1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m⚠️  $1\033[0m"
}

echo "🎲 Board Games Monitor Manager"

case $ACTION in
    "start")
        print_info "Запуск сервисов..."
        docker-compose up -d
        ;;
    "stop")
        print_info "Остановка сервисов..."
        docker-compose down
        ;;
    "restart")
        print_info "Перезапуск сервисов..."
        docker-compose restart
        ;;
    "logs")
        print_info "Логи сервисов..."
        docker-compose logs -f
        ;;
    "status")
        print_info "Статус сервисов:"
        docker-compose ps
        ;;
    "update")
        print_info "Обновление..."
        git pull
        docker-compose build
        docker-compose up -d
        ;;
    "backup")
        print_info "Создание бэкапа..."
        TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
        BACKUP_FILE="backups/backup_${TIMESTAMP}.zip"

        # Создание бэкапа базы данных
        docker-compose exec -T postgres pg_dump -U app app > "backups/db_${TIMESTAMP}.sql"

        # Архивация
        zip -r "$BACKUP_FILE" "backups/db_${TIMESTAMP}.sql"
        rm "backups/db_${TIMESTAMP}.sql"

        print_success "Бэкап создан: $BACKUP_FILE"
        ;;
    *)
        echo "Использование: $0 [start|stop|restart|logs|status|update|backup]"
        exit 1
        ;;
esac

print_success "Готово!"
EOF

    chmod +x manage.sh
    print_success "Скрипт управления создан"
}

# Вывод информации
print_completion_info() {
    echo
    print_success "Установка завершена!"
    echo "================================"
    echo -e "${CYAN}📱 Веб-интерфейс доступен по адресу: http://localhost${NC}"
    echo -e "${CYAN}🔧 API доступен по адресу: http://localhost/api${NC}"
    echo -e "${CYAN}📊 МинIO консоль: http://localhost:9001 (minioadmin/minioadmin)${NC}"
    echo
    echo -e "${YELLOW}📜 Управление сервисами:${NC}"
    echo -e "   ./manage.sh start    - Запустить сервисы"
    echo -e "   ./manage.sh stop     - Остановить сервисы"
    echo -e "   ./manage.sh restart  - Перезапустить сервисы"
    echo -e "   ./manage.sh logs     - Просмотреть логи"
    echo -e "   ./manage.sh status   - Показать статус"
    echo -e "   ./manage.sh update   - Обновить"
    echo -e "   ./manage.sh backup   - Создать бэкап"
    echo
    echo -e "${CYAN}📖 Документация: https://github.com/your-username/board-games-monitor${NC}"
    echo

    if [ "$DEV_MODE" = "true" ]; then
        print_warning "🛠️  Режим разработки:"
        echo -e "   API: http://localhost:8000/docs"
        echo -e "   Frontend: http://localhost:3000"
        echo
    fi

    print_success "✨ Приятного использования!"
}

# Основной процесс
main() {
    print_header

    check_dependencies
    create_install_dir
    clone_repository
    create_env_file
    create_directories
    build_and_start
    wait_for_services
    migrate_database
    create_manage_script
    print_completion_info
}

# Запуск
main "$@"