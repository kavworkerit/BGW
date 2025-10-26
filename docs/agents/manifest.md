# 📋 Манифест агента

Манифест агента - это JSON файл, который описывает конфигурацию, метаданные и параметры работы агента. Система использует манифест для автоматического обнаружения, настройки и запуска агентов.

## 📝 Структура манифеста

### Основные поля

```json
{
  "version": "1.0",
  "id": "unique_agent_id",
  "name": "Человекопонятное название агента",
  "description": "Подробное описание назначения агента",
  "author": "Имя автора или организации",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T12:30:00Z"
}
```

**Обязательные поля:**
- `version` - версия формата манифеста
- `id` - уникальный идентификатор агента
- `name` - название для отображения
- `type` - тип агента
- `entrypoint` - файл точки входа
- `schedule` - расписание запуска

**Опциональные поля:**
- `description` - подробное описание
- `author` - автор агента
- `tags` - теги для категоризации
- `created_at`, `updated_at` - временные метки

### Конфигурация выполнения

```json
{
  "type": "html",
  "entrypoint": "agent.py",
  "schedule": {
    "cron": "0 */2 * * *",
    "timezone": "Europe/Moscow",
    "description": "Каждые 2 часа"
  },
  "rate_limit": {
    "rps": 0.3,
    "burst": 1,
    "daily_pages_cap": 50,
    "description": "Максимально 50 страниц в день"
  }
}
```

**Поля конфигурации:**
- `type` - тип агента (`html`, `api`, `headless`, `telegram_public`)
- `entrypoint` - основной файл агента относительно корня архива
- `schedule` - расписание запуска
- `rate_limit` - ограничения на количество запросов

### Конфигурация агента

```json
{
  "config": {
    "start_urls": ["https://example.com/catalog"],
    "base_url": "https://example.com",
    "selectors": {
      "item": ".product-item",
      "title": ".product-item__title",
      "price": ".product-item__price",
      "url": "a.product-item__link::attr(href)",
      "availability": ".stock-status"
    },
    "price_regex": "([0-9][0-9\\s]+)\\s*₽",
    "max_pages": 10,
    "timeout": 30
  }
}
```

**Поля конфигурации:**
- `start_urls` - начальные URL для обхода
- `base_url` - базовый URL для относительных ссылок
- `selectors` - CSS селекторы для извлечения данных
- `price_regex` - регулярное выражение для парсинга цен
- Другие параметры специфичные для агента

### Секреты и переменные

```json
{
  "secrets": {
    "api_key": {
      "description": "API ключ для доступа к сервису",
      "required": true,
      "default": null
    },
    "username": {
      "description": "Имя пользователя для авторизации",
      "required": false,
      "default": "anonymous"
    },
    "password": {
      "description": "Пароль для авторизации",
      "required": false,
      "default": null
    }
  }
}
```

**Поля секретов:**
- `description` - описание секрета
- `required` - обязательность заполнения
- `default` - значение по умолчанию
- `type` - тип данных (`string`, `number`, `boolean`)

## 🏷️ Метаданные и классификация

### Теги и категории

```json
{
  "tags": ["boardgames", "shop", "preorder"],
  "category": "ecommerce",
  "language": "ru",
  "region": "RU",
  "priority": 10
}
```

**Поля классификации:**
- `tags` - массив тегов для поиска и фильтрации
- `category` - основная категория агента
- `language` - основной язык контента
- `region` - географический регион
- `priority` - приоритет выполнения (чем выше, тем важнее)

### Доступность и зависимости

```json
{
  "requirements": {
    "python": ">=3.8",
    "libraries": ["beautifulsoup4", "requests", "aiohttp"],
    "external_services": ["ollama:11434"]
  },
  "compatibility": {
    "min_bgw_version": "1.0.0",
    "tested_versions": ["1.0.0", "1.1.0"],
    "platforms": ["linux", "windows", "macos"]
  }
}
```

## 📅 Расписание (Schedule)

### Cron формат

```json
{
  "schedule": {
    "cron": "0 */2 * * *",
    "timezone": "Europe/Moscow",
    "description": "Каждые 2 часа"
  }
}
```

**Примеры cron выражений:**
- `"0 */2 * * *"` - каждые 2 часа
- `"0 9,18 * * *"` - в 9:00 и 18:00 ежедневно
- `"0 9 * * 1-5"` - в 9:00 по будням
- `"0 0 1 * *"` - раз в месяц в полночь
- `"*/15 * * * *"` - каждые 15 минут

### Предопределенные расписания

```json
{
  "schedule": {
    "type": "interval",
    "value": 3600,
    "description": "Каждый час"
  }
}
```

**Типы расписаний:**
- `cron` - стандартный cron формат
- `interval` - интервал в секундах
- `daily` - ежедневно в указанное время
- `weekly` - еженедельно
- `monthly` - ежемесячно

## 🚦 Rate Limiting

### Базовые ограничения

```json
{
  "rate_limit": {
    "rps": 0.3,
    "burst": 1,
    "daily_pages_cap": 50,
    "description": "Максимально 50 страниц в день"
  }
}
```

**Параметры:**
- `rps` - запросов в секунду (requests per second)
- `burst` - максимальный пакет запросов
- `daily_pages_cap` - лимит страниц в день
- `description` - описание ограничений

### Продвинутые ограничения

```json
{
  "rate_limit": {
    "rps": 0.5,
    "burst": 2,
    "daily_pages_cap": 100,
    "hourly_limit": 10,
    "minute_limit": 1,
    "retry_after": 300,
    "backoff_factor": 2.0,
    "max_retries": 3
  }
}
```

**Дополнительные параметры:**
- `hourly_limit` - лимит в час
- `minute_limit` - лимит в минуту
- `retry_after` - время между попытками (секунды)
- `backoff_factor` - множитель для экспоненциального бэкоффа
- `max_retries` - максимальное количество повторных попыток

## 🔧 Конфигурация агента

### HTML агенты

```json
{
  "config": {
    "start_urls": [
      "https://store.com/catalog",
      "https://store.com/new-arrivals"
    ],
    "base_url": "https://store.com",
    "user_agent": "BGW-Agent/1.0",
    "headers": {
      "Accept-Language": "ru-RU,ru;q=0.9",
      "Accept": "text/html,application/xhtml+xml"
    },
    "selectors": {
      "item": ".product-card",
      "title": ".product-title",
      "price": ".price-current",
      "original_price": ".price-original",
      "discount": ".discount-badge",
      "availability": ".stock-status",
      "url": ".product-link::attr(href)",
      "image": ".product-image::attr(src)",
      "category": ".product-category"
    },
    "price_regex": "([0-9][0-9\\s]+)\\s*₽",
    "pagination": {
      "type": "page_number",
      "param": "page",
      "max_pages": 20
    },
    "timeout": 30,
    "verify_ssl": true
  }
}
```

### API агенты

```json
{
  "config": {
    "api_base_url": "https://api.store.com/v1",
    "headers": {
      "Authorization": "Bearer ${API_KEY}",
      "Content-Type": "application/json"
    },
    "endpoints": [
      {
        "path": "products",
        "method": "GET",
        "params": {
          "limit": 100,
          "category": "boardgames"
        }
      },
      {
        "path": "products/new",
        "method": "GET",
        "params": {
          "days": 7
        }
      }
    ],
    "pagination": {
      "type": "offset",
      "page_size": 100,
      "max_pages": 10
    },
    "timeout": 15,
    "retry_on_error": true
  }
}
```

### Headless агенты

```json
{
  "config": {
    "urls": ["https://dynamic-store.com/catalog"],
    "wait_for_selector": ".product-list",
    "scroll_to_load": true,
    "screenshot": false,
    "timeout": 30000,
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "javascript": true,
    "cookies": [
      {
        "name": "session_id",
        "value": "${SESSION_ID}",
        "domain": "dynamic-store.com"
      }
    ]
  }
}
```

### Telegram агенты

```json
{
  "config": {
    "channel_username": "boardgames_channel",
    "keywords": [
      "настольная игра",
      "скидка",
      "новинка"
    ],
    "game_keywords": [
      "катан",
      "колонизаторы",
      "громкое дело",
      "каркассон"
    ],
    "max_posts": 50,
    "media_types": ["text", "photo", "video"],
    "filter_by_date": true,
    "days_back": 7
  }
}
```

## 🔒 Безопасность и секреты

### Управление секретами

```json
{
  "secrets": {
    "api_key": {
      "description": "API ключ для доступа к магазину",
      "type": "string",
      "required": true,
      "sensitive": true,
      "validation": {
        "pattern": "^[a-zA-Z0-9]{32,}$",
        "min_length": 32,
        "max_length": 128
      }
    },
    "webhook_url": {
      "description": "URL для вебхуков (опционально)",
      "type": "url",
      "required": false,
      "sensitive": false,
      "validation": {
        "allowed_domains": ["example.com", "webhook.example.com"]
      }
    }
  }
}
```

**Параметры секретов:**
- `type` - тип данных (`string`, `number`, `boolean`, `url`, `email`)
- `required` - обязательность заполнения
- `sensitive` - является ли секретом (скрывается в UI)
- `validation` - правила валидации
- `default` - значение по умолчанию

### Валидация конфигурации

```json
{
  "validation": {
    "required_fields": ["start_urls", "selectors"],
    "field_constraints": {
      "daily_pages_cap": {
        "min": 1,
        "max": 1000
      },
      "rps": {
        "min": 0.1,
        "max": 10.0
      }
    },
    "custom_validators": [
      "validate_url_format",
      "check_selectors_syntax"
    ]
  }
}
```

## 📊 Мониторинг и логирование

### Настройки логирования

```json
{
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "agent.log",
    "max_size": "10MB",
    "backup_count": 5,
    "include_sensitive": false
  }
}
```

### Метрики производительности

```json
{
  "metrics": {
    "enabled": true,
    "export_interval": 60,
    "include": [
      "pages_processed",
      "events_created",
      "errors_count",
      "processing_time",
      "memory_usage"
    ]
  }
}
```

## 🔄 Жизненный цикл агента

### События жизненного цикла

```json
{
  "lifecycle": {
    "on_start": "setup_session",
    "on_success": "send_notification",
    "on_error": "log_error_and_retry",
    "on_finish": "cleanup_resources"
  }
}
```

### Обработка ошибок

```json
{
  "error_handling": {
    "retry_policy": {
      "max_attempts": 3,
      "backoff_strategy": "exponential",
      "initial_delay": 1000,
      "max_delay": 60000
    },
    "fallback_mode": "cache_only",
    "alert_on_failure": true,
    "alert_channels": ["email", "telegram"]
  }
}
```

## 📦 Упаковка и дистрибуция

### Структура архива агента

```
agent.zip
├── manifest.json          # Манифест агента
├── agent.py              # Основной файл агента
├── requirements.txt      # Зависимости Python
├── utils.py             # Вспомогательные функции
├── config.json          # Конфигурация по умолчанию
├── tests/               # Тесты (опционально)
│   ├── test_agent.py
│   └── fixtures/
└── docs/                # Документация (опционально)
    └── README.md
```

### Проверка манифеста

```json
{
  "validation": {
    "schema_version": "1.0",
    "strict_mode": true,
    "required_sections": ["metadata", "schedule", "rate_limit"],
    "deprecated_fields": ["old_api_field"],
    "experimental_features": ["ai_enhancement"]
  }
}
```

## 🛠️ Инструменты и утилиты

### Валидация манифеста

```bash
# Проверка валидности манифеста
bgw validate-manifest manifest.json

# Генерация шаблона манифеста
bgw generate-manifest --type html --template basic

# Конвертация старого формата в новый
bgw migrate-manifest old_manifest.json
```

### Тестирование агента

```json
{
  "testing": {
    "test_urls": ["https://example.com/test-page"],
    "mock_responses": true,
    "expected_events": 5,
    "timeout": 30
  }
}
```

## 📋 Пример полного манифеста

```json
{
  "version": "1.0",
  "id": "hobbygames_coming_soon",
  "name": "Hobby Games — Coming Soon",
  "description": "Мониторинг раздела предзаказов магазина Hobby Games",
  "author": "BGW Team",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T12:30:00Z",

  "type": "html",
  "entrypoint": "agent.py",
  "tags": ["boardgames", "shop", "preorder", "hobbygames"],
  "category": "ecommerce",
  "language": "ru",
  "region": "RU",
  "priority": 10,

  "schedule": {
    "cron": "0 */2 * * *",
    "timezone": "Europe/Moscow",
    "description": "Каждые 2 часа"
  },

  "rate_limit": {
    "rps": 0.3,
    "burst": 1,
    "daily_pages_cap": 50,
    "description": "Максимально 50 страниц в день"
  },

  "config": {
    "start_urls": ["https://hobbygames.ru/coming-soon"],
    "base_url": "https://hobbygames.ru",
    "selectors": {
      "item": ".product-item",
      "title": ".product-item__title",
      "price": ".product-item__price",
      "url": "a.product-item__link::attr(href)",
      "badge": ".product-item__label",
      "availability": ".stock-status"
    },
    "price_regex": "([0-9][0-9\\s]+)\\s*₽",
    "timeout": 30,
    "verify_ssl": true
  },

  "secrets": {
    "api_key": {
      "description": "API ключ для доступа (если требуется)",
      "type": "string",
      "required": false,
      "sensitive": true
    }
  },

  "requirements": {
    "python": ">=3.8",
    "libraries": ["beautifulsoup4", "requests", "lxml"]
  },

  "compatibility": {
    "min_bgw_version": "1.0.0",
    "tested_versions": ["1.0.0", "1.1.0"],
    "platforms": ["linux", "windows", "macos"]
  },

  "logging": {
    "level": "INFO",
    "include_sensitive": false
  },

  "metrics": {
    "enabled": true,
    "export_interval": 60
  },

  "error_handling": {
    "retry_policy": {
      "max_attempts": 3,
      "backoff_strategy": "exponential"
    },
    "alert_on_failure": true
  }
}
```

---

**Используйте этот манифест как шаблон для создания собственных агентов!** 🚀

Следуйте структуре и рекомендациям для обеспечения совместимости и надежной работы агентов в системе BGW.