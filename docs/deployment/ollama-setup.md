# Настройка Ollama для LLM интеграции

## 📋 Обзор

BGW поддерживает интеграцию с Ollama для обработки данных с помощью языковых моделей. LLM используется для:
- Извлечения структурированной информации из текста
- Нормализации названий игр
- Классификации событий
- Генерации синонимов

## 🚀 Установка Ollama

### На хост-машине (для Docker)

1. **Установите Ollama:**
   ```bash
   # Linux/macOS
   curl -fsSL https://ollama.ai/install.sh | sh

   # Или скачайте с https://ollama.ai/download
   ```

2. **Запустите Ollama сервис:**
   ```bash
   ollama serve
   ```

3. **Проверьте работу:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

### В Docker (альтернативно)

Если вы хотите запустить Ollama в Docker:

```yaml
# Добавьте в docker-compose.yml
ollama:
  image: ollama/ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
  restart: unless-stopped

volumes:
  ollama_data:
```

## 🎮 Установка моделей

### Рекомендуемые модели

1. **Llama 3.2 (рекомендуется):**
   ```bash
   ollama pull llama3.2:3b
   ```

2. **Mistral (хорошо для русского):**
   ```bash
   ollama pull mistral
   ```

3. **Qwen (отлично для китайского/русского):**
   ```bash
   ollama pull qwen2.5:3b
   ```

4. **CodeLlama (для технических задач):**
   ```bash
   ollama pull codellama
   ```

### Установка нескольких моделей

```bash
# Основные модели
ollama pull llama3.2:3b
ollama pull mistral
ollama pull qwen2.5:3b

# Проверка установленных моделей
ollama list
```

## ⚙️ Настройка BGW

### 1. Конфигурация URL

Убедитесь, что в `backend/app/core/config.py` указан правильный URL:

```python
OLLAMA_URL: Optional[str] = "http://host.docker.internal:11434"
```

### 2. Переменные окружения

Добавьте в `.env` файл:

```bash
# Ollama settings
OLLAMA_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama3.2:3b
```

### 3. Перезапустите сервисы

```bash
docker-compose restart api worker
```

## 🧪 Тестирование интеграции

### 1. Через API

```bash
# Проверить статус
curl http://localhost:8000/api/llm/status

# Получить модели
curl http://localhost:8000/api/llm/status

# Тест извлечения информации
curl -X POST http://localhost:8000/api/llm/game/extract \
  -H "Content-Type: application/json" \
  -d '{"text": "Громкое дело - новая игра за 2500 ₽"}'
```

### 2. Через веб-интерфейс

1. Откройте BGW в браузере
2. Перейдите в "Настройки" → "LLM (Ollama)"
3. Проверьте статус подключения
4. Протестируйте различные функции

### 3. Через тестовый скрипт

```bash
cd /path/to/BGW
python test_llm.py
```

## 🔧 Использование в агентах

LLM автоматически используется в агентах при низкой уверенности парсинга:

### Пример в агенте:

```python
# В методе parse агента
if self.confidence < 0.7:
    # Используем LLM для улучшения результата
    llm_result = await llm_service.extract_game_info(text)
    if llm_result:
        return self.convert_to_listing_event(llm_result)
```

## 📊 Мониторинг производительности

### Метрики

- Время ответа LLM
- Частота вызовов
- Успешность извлечения данных
- Использование токенов

### Логирование

LLM сервис логирует:
- Успешные/неуспешные запросы
- Время обработки
- Ошибки парсинга ответов

## 🚨 Устранение неисправностей

### Ollama недоступен

1. **Проверьте, что Ollama запущен:**
   ```bash
   ps aux | grep ollama
   ```

2. **Проверьте порт:**
   ```bash
   netstat -tlnp | grep 11434
   ```

3. **Проверьте Docker сетевое взаимодействие:**
   ```bash
   docker run --rm curlimages/curl curl http://host.docker.internal:11434/api/tags
   ```

### Медленные ответы

1. **Используйте более маленькие модели:**
   ```bash
   ollama pull llama3.2:1b
   ```

2. **Настройте температуру в LLM сервисе:**
   ```python
   # В app/services/llm_service.py
   "temperature": 0.1,  # снизьте для более быстрых ответов
   ```

### Некорректные ответы

1. **Проверьте промпты** в `app/services/llm_service.py`
2. **Используйте более мощные модели** для сложных задач
3. **Добавьте примеров в промпты** для лучших результатов

## 🔒 Безопасность

1. **Локальное развертывание** - Ollama работает локально
2. **Нет передачи данных** на внешние сервисы
3. **Контролируемые модели** - вы выбираете какие модели использовать
4. **Изолированная сеть** - Docker изолирует Ollama от внешнего доступа

## 📈 Оптимизация

### Для лучшей производительности:

1. **Выберите подходящую модель:**
   - `llama3.2:1b` - быстрая, базовые задачи
   - `llama3.2:3b` - баланс скорости/качества
   - `mistral` - хорошее качество для русского

2. **Настройте параметры:**
   ```python
   "temperature": 0.1,    # детерминированные ответы
   "max_tokens": 500,     # ограничьте длину
   "top_p": 0.9          # немного разнообразия
   ```

3. **Кэшируйте результаты** для повторяющихся запросов

## 📚 Дополнительные ресурсы

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Available Models](https://ollama.ai/library)
- [Llama 3.2 Models](https://ollama.ai/library/llama3.2)

## 🆘 Поддержка

Если возникли проблемы:

1. Проверьте логи: `docker-compose logs api`
2. Убедитесь, что Ollama запущен и доступен
3. Протестируйте через `test_llm.py`
4. Проверьте конфигурацию сети Docker