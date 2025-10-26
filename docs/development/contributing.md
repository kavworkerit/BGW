# 🤝 Вклад в проект BGW

Спасибо за интерес к проекту BGW (Board Games Watcher)! Мы приветствуем вклады любого уровня - от исправления опечаток до добавления новых функций.

## 🚀 Быстрый старт для контрибьюторов

### 1. Клонирование и настройка

```bash
# Клонируйте репозиторий
git clone https://github.com/kavworkerit/BGW.git
cd BGW

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установите зависимости
pip install -r backend/requirements.txt

# Скопируйте файл окружения
cp .env.example .env
```

### 2. Запуск в режиме разработки

```bash
# Запустите PostgreSQL, Redis и MinIO через Docker
docker-compose up -d postgres redis minio

# Примените миграции базы данных
cd backend
alembic upgrade head

# Запустите бэкенд
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# В другом терминале запустите фронтенд
cd frontend
npm install
npm run dev
```

### 3. Запуск воркеров

```bash
# Worker для фоновых задач
celery -A app.celery_app worker -l INFO

# Beat для планировщика (в третьем терминале)
celery -A app.celery_app beat -l INFO
```

## 📋 Процесс внесения изменений

### Ветка разработки

1. **Создайте ветку** для вашей задачи:
```bash
git checkout -b feature/your-feature-name
# или
git checkout -b fix/issue-description
```

2. **Соблюдайте naming convention**:
- `feature/` - новые функции
- `fix/` - исправления багов
- `docs/` - обновления документации
- `refactor/` - рефакторинг кода
- `test/` - добавление тестов

### Коммиты

Используйте осмысленные сообщения коммитов:

```bash
# ✅ Хорошие примеры
git commit -m "feat: add telegram notifications support"
git commit -m "fix: resolve price history pagination issue"
git commit -m "docs: update API documentation for agents"
git commit -m "test: add unit tests for game matching service"

# ❌ Плохие примеры
git commit -m "fix bug"
git commit -m "update code"
git commit -m "stuff"
```

### Pull Request

1. **Пушьте ветку** в ваш форк:
```bash
git push origin feature/your-feature-name
```

2. **Создайте Pull Request**:
- **Заголовок**: краткое описание изменений
- **Описание**: подробности о том, что и почему изменено
- **Связанные issue**: укажите номера задач, если есть
- **Скриншоты**: для UI изменений

3. **Заполните PR шаблон**:
```markdown
## Описание
Краткое описание внесенных изменений.

## Тип изменений
- [ ] Новая функция
- [ ] Исправление бага
- [ ] Документация
- [ ] Тесты
- [ ] Рефакторинг

## Тестирование
- [ ] Добавлены тесты
- [ ] Все тесты проходят
- [ ] Ручное тестирование проведено

## Проверка
- [ ] Код соответствует style guide
- [ ] Документация обновлена
- [ ] BREAKING CHANGES задокументированы
```

## 🏗️ Структура проекта

### Backend (Python/FastAPI)

```
backend/
├── app/
│   ├── agents/           # Агентная система
│   │   ├── base.py       # Базовые классы
│   │   ├── builtin/      # Встроенные агенты
│   │   └── registry.py   # Реестр агентов
│   ├── api/              # API роуты
│   │   ├── auth.py       # Аутентификация
│   │   ├── games.py      # Управление играми
│   │   └── ...           # Другие роуты
│   ├── core/             # Ядро приложения
│   │   ├── config.py     # Конфигурация
│   │   ├── database.py   # Работа с БД
│   │   └── security.py   # Безопасность
│   ├── models/           # SQLAlchemy модели
│   ├── services/         # Бизнес-логика
│   ├── tasks/            # Celery задачи
│   └── utils/            # Утилиты
├── tests/                # Тесты
├── alembic/              # Миграции БД
└── requirements.txt      # Зависимости
```

### Frontend (React/TypeScript)

```
frontend/
├── src/
│   ├── components/       # React компоненты
│   │   ├── Layout/       # Компоновка
│   │   ├── GameForm/     # Формы игр
│   │   └── ...           # Другие компоненты
│   ├── pages/            # Страницы приложения
│   ├── services/         # API клиенты
│   ├── store/            # Zustand state
│   ├── types/            # TypeScript типы
│   └── utils/            # Утилиты
├── public/               # Статические файлы
└── package.json          # Зависимости
```

## 🧪 Тестирование

### Запуск тестов

```bash
# Backend тесты
cd backend
pytest                    # Все тесты
pytest --cov=app          # С покрытием
pytest tests/test_agents.py # Конкретный модуль

# Frontend тесты
cd frontend
npm test                  # Все тесты
npm test -- --coverage    # С покрытием
```

### Написание тестов

#### Backend тесты

```python
# tests/test_game_service.py
import pytest
from app.services.game_service import GameService

@pytest.mark.asyncio
async def test_create_game():
    service = GameService()
    game_data = {
        "title": "Тестовая игра",
        "publisher": "Тестовый издатель"
    }

    game = await service.create_game(game_data)

    assert game.title == "Тестовая игра"
    assert game.publisher == "Тестовый издатель"
```

#### Frontend тесты

```typescript
// src/components/__tests__/GameCard.test.tsx
import { render, screen } from '@testing-library/react';
import GameCard from '../GameCard';

test('renders game card with title', () => {
  const game = { title: 'Test Game', price: 1000 };
  render(<GameCard game={game} />);

  expect(screen.getByText('Test Game')).toBeInTheDocument();
  expect(screen.getByText('1000₽')).toBeInTheDocument();
});
```

## 🎨 Код стайл и стандарты

### Backend (Python)

Используйте **Black** для форматирования и **isort** для сортировки импортов:

```bash
# Форматирование кода
black app/
isort app/

# Проверка стиля
flake8 app/
mypy app/
```

**Правила:**
- Максимум 88 символов в строке
- Используйте type hints
- Docstrings для всех функций и классов
- Имена переменных: `snake_case`
- Имена классов: `PascalCase`

### Frontend (TypeScript/React)

```bash
# Линтинг
npm run lint
npm run lint:fix

# Проверка типов
npm run type-check
```

**Правила:**
- Используйте Prettier для форматирования
- Имена компонентов: `PascalCase`
- Имена переменных/функций: `camelCase`
- Используйте TypeScript строго
- Хуки в начале функциональных компонентов

## 🐛 Отладка

### Backend отладка

```python
# В коде
import logging
logger = logging.getLogger(__name__)

logger.info("Информационное сообщение")
logger.debug("Отладочная информация")
logger.error("Ошибка")

# Точки остановки в VS Code
import pdb; pdb.set_trace()
```

### Frontend отладка

```typescript
// Консоль логирование
console.log('Debug info:', data);

// React DevTools
// Redux DevTools (если используется)
```

## 📝 Документация

### Обновление документации

1. **API документация** обновляется автоматически через FastAPI
2. **Пользовательская документация** в `docs/user-guide/`
3. **Документация для разработчиков** в `docs/development/`
4. **Комментарии в коде** для сложной логики

### Примеры документации

```python
def calculate_game_price(base_price: float, discount: float) -> float:
    """
    Рассчитывает итоговую цену игры с учетом скидки.

    Args:
        base_price: Базовая цена игры
        discount: Процент скидки (0-100)

    Returns:
        Итоговая цена с учетом скидки

    Raises:
        ValueError: если цена отрицательная или скидка > 100%
    """
    if discount < 0 or discount > 100:
        raise ValueError("Скидка должна быть в диапазоне 0-100")

    final_price = base_price * (1 - discount / 100)
    return max(0, final_price)
```

## 🚨 Common issues и решения

### Проблемы с базой данных

```bash
# Сброс миграций
alembic downgrade base
alembic upgrade head

# Проверка соединения
docker-compose exec postgres psql -U app -d app
```

### Проблемы с Celery

```bash
# Проверка статуса воркеров
celery -A app.celery_app inspect active

# Перезапуск воркеров
pkill -f "celery.*worker"
celery -A app.celery_app worker -l INFO
```

### Frontend проблемы

```bash
# Очистка кэша
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

## 🏷️ Labeling и triage

### Labels для Pull Request

- `ready for review` - готов к ревью
- `work in progress` - в разработке
- `documentation` - изменения в документации
- `bug fix` - исправление бага
- `feature` - новая функция
- `testing` - изменения в тестах
- `dependencies` - обновление зависимостей

### Priority levels

- `critical` - критические баги, блокирующие релиз
- `high` - важные функции, срочные исправления
- `medium` - стандартные улучшения
- `low` - незначительные улучшения, оптимизации

## 📋 Code Review Guidelines

### Для ревьюверов

1. **Проверьте функциональность** - работает ли как ожидается
2. **Проверьте стиль кода** - соответствует ли стандартам
3. **Проверьте тесты** - добавлены ли и проходят ли
4. **Проверьте документацию** - обновлена ли
5. **Проверьте безопасность** - нет ли уязвимостей

### Для авторов

1. **Саморевью** перед отправкой на ревью
2. **Ответьте на все комментарии** ревьюверов
3. **Внесите правки** по итогам ревью
4. **Обновите PR** после изменений

## 🔄 Release Process

### Подготовка к релизу

1. **Обновите версию** в `package.json` и `backend/requirements.txt`
2. **Обновите CHANGELOG.md** с описанием изменений
3. **Проверьте все тесты** проходят
4. **Создайте release tag**
5. **Соберите Docker образы**

### Post-release

1. **Мониторинг** после релиза
2. **Отслеживание** обратной связи
3. **Быстрое исправление** критических багов

## 🎯 Рекомендуемые задачи для новичков

### Good First Issues

1. **Исправление опечаток** в документации
2. **Добавление тестов** для существующего кода
3. **Улучшение сообщений об ошибках**
4. **Обновление зависимостей**
5. **Рефакторинг небольших функций**

### Feature идеи

1. **Новые агенты** для других магазинов
2. **Улучшение UI/UX** фронтенда
3. **Дополнительная аналитика**
4. **Интеграции** с внешними сервисами
5. **Мобильное приложение**

## 📞 Контакты и поддержка

### Куда обращаться за помощью

- **GitHub Issues** - для багов и вопросов
- **GitHub Discussions** - для обсуждений
- **Telegram чат** - для неформального общения
- **Email** - для конфиденциальных вопросов

### Этические нормы

- **Уважайте других** контрибьютеров
- **Будьте конструктивны** в отзывах
- **Помогайте новичкам** освоиться
- **Следуйте Code of Conduct**

---

**Спасибо за ваш вклад в развитие BGW!** 🎲✨

Каждый вклад помогает сделать систему лучше для всего сообщества любителей настольных игр.