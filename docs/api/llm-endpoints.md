# 🤖 LLM API Документация

## Обзор

BGW предоставляет полноценный LLM API для интеграции с Ollama и другими языковыми моделями. API позволяет использовать AI для анализа, нормализации и обогащения данных о настольных играх.

**Base URL**: `http://localhost:8000/api/v1/llm`

## 📋 Эндпоинты

### 1. Статус LLM сервиса

```http
GET /llm/status
```

Проверяет доступность LLM сервиса и возвращает текущую конфигурацию.

**Response:**
```json
{
  "available": true,
  "url": "http://localhost:11434",
  "models": ["llama3.1:8b", "mistral:7b", "qwen:7b"],
  "current_model": "llama3.1:8b",
  "error": null
}
```

**Поля ответа:**
- `available` - доступность сервиса
- `url` - URL Ollama API
- `models` - список доступных моделей
- `current_model` - текущая активная модель
- `error` - описание ошибки если сервис недоступен

### 2. Тестирование LLM

```http
POST /llm/test
```

Универсальный эндпоинт для тестирования различных задач LLM.

**Request Body:**
```json
{
  "text": "Громкое дело - отличная экономическая стратегия для 2-5 игроков",
  "task": "extract_game_info"
}
```

**Доступные задачи:**
- `extract_game_info` - извлечение информации об игре
- `normalize_title` - нормализация названия
- `categorize_event` - категоризация события
- `suggest_synonyms` - генерация синонимов

**Response:**
```json
{
  "success": true,
  "result": {
    "title": "Громкое дело",
    "description": "Экономическая стратегия",
    "players_min": 2,
    "players_max": 5,
    "playing_time": "45-60 минут",
    "age": "12+"
  },
  "processing_time": 2.34
}
```

### 3. Переключение модели

```http
POST /llm/models/switch
```

Переключает активную модель LLM.

**Query параметры:**
- `model_name: str` - название модели для переключения

**Response:**
```json
{
  "success": true,
  "model": "mistral:7b",
  "message": "Switched to model: mistral:7b"
}
```

### 4. Извлечение информации об игре

```http
POST /llm/game/extract
```

Извлекает структурированную информацию об игре из текста.

**Query параметры:**
- `text: str` - текст для анализа
- `html_fragment: str = ""` - опциональный HTML контекст

**Response:**
```json
{
  "success": true,
  "result": {
    "title": "Громкое дело",
    "description": "Игра про ограбление поезда на Диком Западе",
    "players_min": 2,
    "players_max": 5,
    "playing_time": "45-60",
    "age": "12+",
    "publisher": "Hobby Games",
    "year": "2023",
    "category": "Экономическая стратегия"
  }
}
```

### 5. Нормализация названия

```http
POST /llm/game/normalize
```

Нормализует название игры, удаляя лишние элементы.

**Body:** `title: str`

**Response:**
```json
{
  "success": true,
  "original": "Громкое дело (новое издание, 2024) - SALE!",
  "normalized": "Громкое дело"
}
```

**Примеры нормализации:**
- `"Громкое дело (новое издание)"` → `"Громкое дело"`
- `"Колонизаторы -30% распродажа"` → `"Колонизаторы"`
- `"Catan: Звезды/"` → `"Catan: Звезды"`

### 6. Генерация синонимов

```http
POST /llm/game/synonyms
```

Генерирует синонимы и альтернативные названия для улучшенного поиска.

**Query параметры:**
- `title: str` - название игры
- `description: str = ""` - описание для контекста

**Response:**
```json
{
  "success": true,
  "title": "Громкое дело",
  "synonyms": [
    "Поезд",
    "Ограбление поезда",
    "Great Train Robbery",
    "Громко Дело",
    "Train Heist"
  ],
  "count": 5
}
```

### 7. Категоризация события

```http
POST /llm/event/categorize
```

Определяет тип события на основе заголовка и описания.

**Query параметры:**
- `title: str` - заголовок события
- `description: str = ""` - описание

**Response:**
```json
{
  "success": true,
  "title": "Громкое дело - предзаказ открылся!",
  "event_type": "preorder"
}
```

**Типы событий:**
- `release` - релиз игры
- `preorder` - открытие предзаказа
- `restock` - пополнение склада
- `sale` - скидка/распродажа

## 🔧 Конфигурация

### Переменные окружения

```bash
# Ollama конфигурация
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
OLLAMA_TIMEOUT=30

# LLM сервис
LLM_ENABLED=true
LLM_CACHE_TTL=3600
```

### Поддерживаемые модели

- **llama3.1:8b** - основная модель, баланс качества и скорости
- **mistral:7b** - быстрая модель для простых задач
- **qwen:7b** - хороша с китайским и многоязычными текстами
- **codegemma:7b** - специализируется на структурированных данных

## 📝 Примеры использования

### Python

```python
import requests

base_url = "http://localhost:8000/api/v1"

# Проверка статуса
status = requests.get(f"{base_url}/llm/status").json()
if status["available"]:
    print(f"Доступные модели: {status['models']}")

# Извлечение информации
game_info = requests.post(
    f"{base_url}/llm/game/extract",
    params={"text": "Громкое дело - экономическая стратегия про ограбление поезда"}
).json()

# Генерация синонимов
synonyms = requests.post(
    f"{base_url}/llm/game/synonyms",
    params={"title": "Громкое дело", "description": "Игра про ограбление поезда"}
).json()
```

### JavaScript

```javascript
// Нормализация названия
const normalizeTitle = async (title) => {
  const response = await fetch('/api/v1/llm/game/normalize', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({title})
  });
  return await response.json();
};

// Извлечение информации
const extractGameInfo = async (text) => {
  const response = await fetch('/api/v1/llm/game/extract', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text})
  });
  return await response.json();
};
```

### cURL

```bash
# Статус LLM
curl -X GET http://localhost:8000/api/v1/llm/status

# Извлечение информации
curl -X POST http://localhost:8000/api/v1/llm/game/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Громкое дело - отличная экономическая стратегия"}'

# Переключение модели
curl -X POST "http://localhost:8000/api/v1/llm/models/switch?model_name=mistral:7b"
```

## 🚨 Ошибки и обработка

### Common ошибки

**400 Bad Request**
```json
{
  "success": false,
  "error": "LLM service not available"
}
```

**500 Internal Server Error**
```json
{
  "success": false,
  "error": "Failed to extract game info: Connection timeout"
}
```

### Рекомендации по обработке

1. **Всегда проверяйте статус** перед использованием
2. **Используйте try-catch** для обработки ошибок
3. **Устанавливайте таймауты** для LLM запросов
4. **Кэшируйте результаты** для повторных запросов

## 🎯 Use Cases

### 1. Автоматическое обогащение данных
```python
# При добавлении новой игры
game_data = {
    "title": "Громкое дело (новое издание) -30%",
    "price": 2090,
    "store": "Hobby Games"
}

# Нормализуем название
normalized = requests.post("/api/v1/llm/game/normalize",
    json={"title": game_data["title"]})
game_data["normalized_title"] = normalized.json()["normalized"]

# Извлекаем информацию
info = requests.post("/api/v1/llm/game/extract",
    json={"text": game_data["title"]})
if info.json()["success"]:
    game_data.update(info.json()["result"])
```

### 2. Улучшение поиска
```python
# Генерация синонимов для улучшения поиска
def enhance_search_query(title):
    synonyms_response = requests.post("/api/v1/llm/game/synonyms",
        json={"title": title})
    if synonyms_response.json()["success"]:
        synonyms = synonyms_response.json()["synonyms"]
        # Включаем синонимы в поиск
        return [title] + synonyms
    return [title]

# Поиск с синонимами
search_terms = enhance_search_query("Громкое дело")
for term in search_terms:
    results += search_games(term)
```

### 3. Категоризация событий
```python
# Автоматическое определение типа события
def categorize_listing(title, description=""):
    response = requests.post("/api/v1/llm/event/categorize",
        json={"title": title, "description": description})

    if response.json()["success"]:
        return response.json()["event_type"]
    return "unknown"  # fallback
```

## 🔒 Безопасность и ограничения

### Ограничения
- **30 запросов/минута** на LLM эндпоинты
- **30 секунд** таймаут на выполнение
- **10,000 символов** максимальный размер текста

### Безопасность
- Валидация всех входных данных
- Sanitизация HTML контента
- Rate limiting по IP адресу
- Логирование всех запросов

---

Дополнительная информация:
- [📋 Основное API](./endpoints.md)
- [🔧 Конфигурация Ollama](../deployment/ollama.md)
- [🧪 Примеры использования](../examples/llm-integration.md)