# 📦 Export/Import API Документация

## Обзор

BGW предоставляет мощный API для экспорта и импорта данных системы, поддерживающий полный бэкап и восстановление, а также экспорт в CSV для внешнего анализа.

**Base URL**: `http://localhost:8000/api/v1/export`

## 📋 Эндпоинты

### 1. Полный экспорт данных

```http
GET /export/full
```

Создает полный ZIP архив со всеми данными системы.

**Query параметры:**
- `include_raw_data: bool = false` - включать сырые данные парсинга

**Response:** ZIP архив со следующей структурой:
```
bgw_export.zip
├── games.json          # Игры и их метаданные
├── rules.json          # Правила уведомлений
├── events.json         # События (релизы, скидки, etc.)
├── price_history.json  # История цен
├── metadata.json       # Метаданные экспорта
└── raw_data/          # Сырые данные (если включено)
    ├── raw_items.json
    └── listings/
```

**Пример metadata.json:**
```json
{
  "version": "1.0.0",
  "created_at": "2024-01-15T12:30:00Z",
  "created_by": "BGW Export Service",
  "checksum": "sha256:abc123def456...",
  "contents": {
    "games_count": 1250,
    "rules_count": 8,
    "events_count": 5420,
    "price_history_count": 15420,
    "include_raw_data": false
  }
}
```

### 2. Полный импорт данных

```http
POST /export/full
```

Импортирует данные из ZIP архива.

**Query параметры:**
- `dry_run: bool = true` - тестовый режим без применения изменений

**Request:** multipart/form-data с файлом ZIP

**Response (dry_run=true):**
```json
{
  "success": true,
  "dry_run": true,
  "summary": {
    "games": {
      "new": 25,
      "updated": 12,
      "skipped": 3,
      "errors": 1
    },
    "rules": {
      "new": 2,
      "updated": 1,
      "skipped": 0,
      "errors": 0
    },
    "events": {
      "new": 150,
      "updated": 0,
      "skipped": 25,
      "errors": 2
    },
    "price_history": {
      "new": 450,
      "updated": 80,
      "skipped": 15,
      "errors": 0
    }
  },
  "warnings": [
    "Game with duplicate title skipped: 'Громкое дело'",
    "Rule with invalid conditions skipped: 'Test rule'"
  ],
  "errors": [
    "Failed to process event: Invalid price format",
    "Database constraint violation for game ID"
  ]
}
```

**Response (dry_run=false):**
```json
{
  "success": true,
  "dry_run": false,
  "applied": true,
  "summary": {
    "games": {"new": 25, "updated": 12, "skipped": 3, "errors": 0},
    "rules": {"new": 2, "updated": 1, "skipped": 0, "errors": 0},
    "events": {"new": 150, "updated": 0, "skipped": 25, "errors": 0},
    "price_history": {"new": 450, "updated": 80, "skipped": 15, "errors": 0}
  },
  "import_id": "import-uuid-123",
  "duration_seconds": 45.2
}
```

### 3. Анализ импорта

```http
POST /export/summary
```

Анализирует ZIP архив без выполнения импорта.

**Request:** multipart/form-data с файлом ZIP

**Response:**
```json
{
  "version": "1.0.0",
  "created_at": "2024-01-15T12:30:00Z",
  "checksum": "sha256:abc123def456...",
  "size_mb": 25.4,
  "contents": {
    "games_count": 1250,
    "rules_count": 8,
    "events_count": 5420,
    "price_history_count": 15420,
    "includes_raw_data": true
  },
  "compatibility": {
    "compatible": true,
    "version_match": true,
    "warnings": ["Import from newer version 1.1.0"]
  },
  "preview": {
    "sample_games": [
      {
        "title": "Громкое дело",
        "store": "Hobby Games",
        "price": 2990
      }
    ],
    "date_range": {
      "earliest_event": "2023-01-01",
      "latest_event": "2024-01-15"
    }
  }
}
```

### 4. Экспорт игр в CSV

```http
GET /export/games/csv
```

Экспортирует игры в CSV формате для анализа в Excel/Google Sheets.

**Query параметры:**
- `game_ids: str = ""` - ID игр через запятую (пусто = все игры)

**Response:** CSV файл с заголовками:
```csv
id,title,store,price,url,created_at,updated_at,description,players_min,players_max,playing_time,age,publisher,year,category,bgg_id
"550e8400-e29b-41d4-a716-446655440000","Громкое дело","Hobby Games",2990,"https://hobbygames.ru/...","2024-01-01T12:00:00Z","2024-01-15T14:30:00Z","Экономическая стратегия про ограбление поезда",2,5,"45-60","12+","Hobby Games",2023,"Экономическая стратегия",12345
```

### 5. Экспорт истории цен в CSV

```http
GET /export/price-history/{game_id}/csv
```

Экспортирует историю цен конкретной игры.

**Query параметры:**
- `days: int = 365` - период в днях (1-3650)

**Response:** CSV файл:
```csv
timestamp,price,previous_price,discount_pct,url,store
"2024-01-15T12:00:00Z",2990,3990,25,"https://hobbygames.ru/...","Hobby Games"
"2024-01-10T09:30:00Z",3990,null,0,"https://hobbygames.ru/...","Hobby Games"
"2023-12-20T15:45:00Z",4490,null,0,"https://hobbygames.ru/...","Hobby Games"
```

## 📝 Форматы данных

### games.json
```json
{
  "games": [
    {
      "id": "uuid",
      "title": "Громкое дело",
      "normalized_title": "Громкое дело",
      "description": "Экономическая стратегия...",
      "store": "Hobby Games",
      "price": 2990,
      "url": "https://...",
      "image_url": "https://...",
      "players_min": 2,
      "players_max": 5,
      "playing_time": "45-60",
      "age": "12+",
      "publisher": "Hobby Games",
      "year": 2023,
      "category": "Экономическая стратегия",
      "bgg_id": 12345,
      "synonyms": ["Поезд", "Ограбление поезда"],
      "in_watchlist": true,
      "created_at": "2024-01-01T12:00:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ]
}
```

### rules.json
```json
{
  "rules": [
    {
      "id": "uuid",
      "name": "Большие скидки",
      "description": "Уведомлять о скидках > 20%",
      "logic": "AND",
      "conditions": [
        {"field": "discount_pct", "op": ">=", "value": 20},
        {"field": "price", "op": "<=", "value": 5000}
      ],
      "channels": ["webpush", "telegram"],
      "cooldown_hours": 12,
      "active": true,
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### events.json
```json
{
  "events": [
    {
      "id": "uuid",
      "game_id": "uuid",
      "kind": "sale",
      "title": "Громкое дело -25% на ограбление поезда!",
      "description": "Отличная скидка на популярную игру",
      "price": 2990,
      "previous_price": 3990,
      "discount_pct": 25,
      "url": "https://...",
      "store": "Hobby Games",
      "image_url": "https://...",
      "processed": true,
      "created_at": "2024-01-15T12:00:00Z"
    }
  ]
}
```

## 🔧 Примеры использования

### Python

```python
import requests
import json
from datetime import datetime

base_url = "http://localhost:8000/api/v1"

# Полный экспорт
def export_full_backup():
    response = requests.get(f"{base_url}/export/full", params={
        "include_raw_data": True
    })

    if response.status_code == 200:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"bgw_backup_{timestamp}.zip"

        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"Экспорт сохранен: {filename}")
    else:
        print(f"Ошибка экспорта: {response.status_code}")

# Импорт с проверкой
def import_backup(file_path, dry_run=True):
    with open(file_path, "rb") as f:
        files = {"file": f}
        params = {"dry_run": dry_run}

        response = requests.post(f"{base_url}/export/full",
                               files=files, params=params)
        result = response.json()

        if dry_run:
            print("Анализ импорта:")
            print(json.dumps(result["summary"], indent=2))
            if result.get("warnings"):
                print("Предупреждения:", result["warnings"])
        else:
            print("Импорт выполнен:", result["success"])

# Экспорт конкретных игр в CSV
def export_games_csv(game_ids):
    ids_str = ",".join(game_ids)
    response = requests.get(f"{base_url}/export/games/csv",
                          params={"game_ids": ids_str})

    if response.status_code == 200:
        filename = "selected_games.csv"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"CSV сохранен: {filename}")
```

### JavaScript

```javascript
// Экспорт через браузер
async function exportFullBackup(includeRawData = false) {
  try {
    const response = await fetch(`/api/v1/export/full?include_raw_data=${includeRawData}`);

    if (response.ok) {
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `bgw_backup_${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } else {
      console.error('Ошибка экспорта:', response.status);
    }
  } catch (error) {
    console.error('Ошибка при экспорте:', error);
  }
}

// Анализ импорта
async function analyzeImport(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/v1/export/summary', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();

  if (result.compatibility?.compatible) {
    console.log('Файл совместим');
    console.log('Содержимое:', result.contents);
    return true;
  } else {
    console.error('Файл несовместим:', result.compatibility);
    return false;
  }
}
```

### cURL

```bash
# Полный экспорт
curl -X GET "http://localhost:8000/api/v1/export/full?include_raw_data=true" \
  -o "bgw_backup.zip"

# Анализ импорта
curl -X POST http://localhost:8000/api/v1/export/summary \
  -F "file=@bgw_backup.zip"

# Импорт (dry run)
curl -X POST "http://localhost:8000/api/v1/export/full?dry_run=true" \
  -F "file=@bgw_backup.zip"

# Экспорт игр в CSV
curl -X GET "http://localhost:8000/api/v1/export/games/csv" \
  -o "games.csv"

# Экспорт истории цен
curl -X GET "http://localhost:8000/api/v1/export/price-history/uuid/csv?days=90" \
  -o "price_history.csv"
```

## 🚨 Ограничения и рекомендации

### Ограничения
- **Размер файла**: до 100MB для импорта
- **Частота**: 10 экспортов/час на IP
- **Таймаут**: 5 минут для больших экспортов
- **Формат**: только ZIP архивы

### Рекомендации

#### Регулярные бэкапы
```python
# Автоматический бэкап каждое утро
import schedule
import time

def daily_backup():
    export_full_backup()

schedule.every().day.at("06:00").do(daily_backup)

while True:
    schedule.run_pending()
    time.sleep(60)
```

#### Валидация перед импортом
```python
def safe_import(file_path):
    # Сначала анализируем
    with open(file_path, "rb") as f:
        files = {"file": f}
        summary = requests.post(f"{base_url}/export/summary",
                              files=files).json()

    # Проверяем совместимость
    if not summary.get("compatibility", {}).get("compatible"):
        print("Файл несовместим!")
        return False

    # Запускаем dry run
    import_backup(file_path, dry_run=True)

    # Запрашиваем подтверждение
    if input("Выполнить импорт? (y/n): ").lower() == 'y':
        import_backup(file_path, dry_run=False)
        return True

    return False
```

#### Оптимизация экспорта
```python
# Экспорт только измененных данных
def export_incremental(days=7):
    response = requests.get(f"{base_url}/export/games/csv", params={
        "game_ids": get_recently_updated_games(days)
    })
    # ... обработка ответа
```

## 📊 Статистика и мониторинг

### Метрики экспорта/импорта
```http
GET /metrics
```

Prometheus метрики:
```
export_operations_total{type="full",status="success"} 15
export_operations_total{type="csv",status="success"} 45
import_operations_total{type="full",status="success"} 8
import_operations_total{type="full",status="failed"} 1
export_data_bytes_total 1073741824
```

---

Дополнительная информация:
- [📋 Основное API](./endpoints.md)
- 🤖 [LLM API](./llm-endpoints.md)
- [🔧 Конфигурация бэкапов](../deployment/backup.md)