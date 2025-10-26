# Тесты BGW Backend

## Структура тестов

- `test_agents.py` - Базовые тесты для всех агентов
- `test_agent_record_replay.py` - Тесты с записанными HTTP запросами (VCR.py)
- `test_api.py` - Интеграционные тесты API эндпоинтов

## Установка и запуск

### 1. Установка зависимостей

```bash
# В директории backend
python3 -m venv test_env
source test_env/bin/activate

# Установка зависимостей включая тестовые
pip install -r requirements.txt pytest pytest-asyncio pytest-cov pytest-mock factory-boy faker
```

### 2. Запуск тестов

```bash
# Все тесты
pytest

# Только тесты агентов
pytest -m agents

# Только тесты API
pytest -m api

# Быстрые тесты (без медленных)
pytest -m "not slow"

# С покрытием кода
pytest --cov=app --cov-report=html

# Отдельные тесты
pytest tests/test_agents.py::TestBaseAgent::test_base_agent_is_abstract -v
```

### 3. Создание новых кассет VCR

Для записи реальных HTTP запросов:

```bash
# Установить VCR
pip install vcrpy

# Запустить тесты с записью
pytest tests/test_agent_record_replay.py --record-mode=new_episodes
```

## Типы тестов

### `@pytest.mark.agents`
Тесты для веб-скрейпинг агентов:
- Инициализация агентов
- Валидация конфигурации
- Парсинг HTML
- Обработка ошибок
- Rate limiting

### `@pytest.mark.api`
Тесты REST API:
- CRUD операции
- Валидация данных
- Обработка ошибок
- Интеграционные сценарии

### `@pytest.mark.unit`
Юнит-тесты:
- Тест отдельных функций
- Моки зависимостей
- Быстрое выполнение

### `@pytest.mark.integration`
Интеграционные тесты:
- Тест нескольких компонентов вместе
- Реальные HTTP запросы (через VCR)
- Медленные тесты

### `@pytest.mark.slow`
Медленные тесты:
- Запросы к реальным сайтам
- Интеграционные сценарии
- Пропускаются по умолчанию

## Ожидаемое покрытие

- **Базовые классы**: 90%
- **Агенты**: 80%+
- **API**: 85%+
- **Сервисы**: 75%+

## Continuous Integration

Тесты автоматически запускаются в CI/CD с:

```yaml
test:
  script:
    - pytest --cov=app --cov-fail-under=75
  artifacts:
    reports:
      junit: test-results.xml
      coverage: coverage/html/
```

## Best Practices

1. **Использовать fixtures** для общих данных
2. **Изолировать тесты** друг от друга
3. **Мокать внешние зависимости**
4. **Использовать descriptive имена** тестов
5. **Тестировать граничные случаи** (пустые данные, ошибки)
6. **Использовать VCR** для реальных HTTP запросов
7. **Писать assertion messages** на русском

## Примеры

### Базовый тест агента:
```python
@pytest.mark.agents
def test_agent_initialization(self, sample_config, sample_secrets):
    ctx = Mock(spec=RuntimeContext)
    agent = HobbyGamesAgent(sample_config, sample_secrets, ctx)

    assert agent.TYPE == "html"
    assert agent.config == sample_config
```

### Тест API:
```python
@pytest.mark.api
def test_create_game_success(self, client, mock_db):
    game_data = {"title": "Тестовая игра"}

    with patch('app.api.games.get_db', return_value=mock_db):
        response = client.post("/api/games", json=game_data)

        assert response.status_code == 201
        assert response.json()["title"] == game_data["title"]
```

### Тест с VCR:
```python
@vcr.use_cassette("hobbygames.yaml")
@pytest.mark.asyncio
async def test_real_fetch(self):
    # Запись или воспроизведение реальных запросов
    pass
```