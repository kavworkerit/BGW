# Вклад в проект Board Games Monitor

Спасибо за интерес к проекту! Этот документ поможет вам начать внесение вклада.

## 🚀 Как начать

### Предварительные требования

- Docker и Docker Compose
- Python 3.11+
- Node.js 18+
- Git

### Настройка окружения для разработки

1. **Форкните репозиторий**
   ```bash
   git clone https://github.com/your-username/board-games-monitor.git
   cd board-games-monitor
   ```

2. **Настройте окружение**
   ```bash
   cp .env.example .env
   # Отредактируйте .env при необходимости
   ```

3. **Запустите сервисы**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

4. **Установите зависимости**
   ```bash
   # Backend
   cd backend
   pip install -r requirements.txt
   pip install -r requirements-dev.txt

   # Frontend
   cd ../frontend
   npm install
   ```

## 🏗️ Структура проекта

```
├── backend/                 # FastAPI приложение
│   ├── app/
│   │   ├── agents/         # Агентная платформа
│   │   │   ├── base.py     # Базовый класс агента
│   │   │   ├── registry.py # Реестр агентов
│   │   │   └── builtin/    # Встроенные агенты
│   │   ├── api/            # API роутеры
│   │   ├── models/         # SQLAlchemy модели
│   │   ├── services/       # Бизнес-логика
│   │   ├── tasks/          # Celery задачи
│   │   └── schemas/        # Pydantic схемы
│   ├── tests/              # Тесты
│   └── alembic/            # Миграции БД
├── frontend/               # React приложение
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── pages/          # Страницы
│   │   ├── services/       # API сервисы
│   │   └── utils/          # Утилиты
│   └── public/
├── agents/                 # Манифесты агентов
├── deploy/                 # Конфигурации для деплоя
└── docs/                   # Документация
```

## 🤝 Внесение изменений

### Branch Strategy

- `main` - стабильная версия
- `develop` - ветка разработки
- `feature/*` - новые функции
- `bugfix/*` - исправления ошибок
- `hotfix/*` - срочные исправления

### Process

1. **Создайте branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Внесите изменения**
   - Следуйте существующему стилю кода
   - Добавьте тесты для новых функций
   - Обновите документацию

3. **Commit изменения**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```

4. **Push и создайте Pull Request**
   ```bash
   git push origin feature/amazing-feature
   ```

### Сообщения коммитов

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` новая функция
- `fix:` исправление ошибки
- `docs:` документация
- `style:` форматирование кода
- `refactor:` рефакторинг
- `test:` тесты
- `chore:` обслуживание

## 🧪 Тестирование

### Backend тесты

```bash
cd backend
pytest
pytest --cov=app tests/
```

### Frontend тесты

```bash
cd frontend
npm test
npm run test:coverage
```

### E2E тесты

```bash
npm run test:e2e
```

## 📝 Добавление новых агентов

1. **Создайте класс агента**
   ```python
   # backend/app/agents/builtin/myagent.py
   from app.agents.base import HTMLAgent

   class MyAgent(HTMLAgent):
       async def parse(self, fetched):
           # Реализация парсинга
           pass
   ```

2. **Зарегистрируйте агент**
   ```python
   # backend/app/agents/builtin/__init__.py
   from .myagent import MyAgent
   ```

3. **Добавьте тесты**
   ```python
   # backend/tests/test_agents/test_myagent.py
   ```

4. **Создайте манифест**
   ```json
   {
     "id": "myagent",
     "name": "My Agent",
     "type": "html",
     "config": {...}
   }
   ```

## 🔧 Code Style

### Python (Backend)

- Используйте `black` для форматирования
- Используйте `flake8` для линтинга
- Следуйте PEP 8

```bash
black app/
flake8 app/
```

### TypeScript/JavaScript (Frontend)

- Используйте Prettier для форматирования
- Используйте ESLint для линтинга

```bash
npm run lint
npm run format
```

## 📖 Документация

- API документация генерируется автоматически через FastAPI
- Обновляйте README.md при значительных изменениях
- Добавляйте комментарии в сложном коде
- Создавайте документацию для новых функций

## 🐛 Отчеты об ошибках

При создании issue используйте шаблон:

1. **Описание ошибки**
2. **Шаги воспроизведения**
3. **Ожидаемое поведение**
4. **Фактическое поведение**
5. **Окружение** (OS, Docker version, etc.)
6. **Логи** (если применимо)

## 💡 Предложения функций

При создании feature request:

1. **Описание функции**
2. **Проблема, которую она решает**
3. **Предлагаемое решение**
4. **Альтернативные решения**
5. **Дополнительная информация**

## 🔍 Code Review

### Review Guidelines

1. **Проверьте функциональность**
   - Работает ли код как ожидалось?
   - Есть ли edge cases?

2. **Проверьте качество кода**
   - Следует ли код стилю проекта?
   - Понятны ли имена переменных/функций?
   - Есть ли комментарии где нужно?

3. **Проверьте тесты**
   - Покрывают ли тесты новый код?
   - Есть ли тесты на edge cases?

4. **Проверьте документацию**
   - Обновлена ли документация?
   - Понятны ли коммиты?

### Review Process

1. Автоматические проверки пройдены
2. Минимум один approval от мейнтейнера
3. Все комментарии обсуждены и решены
4. CI/CD проходит успешно

## 🚀 Выпуск релизов

### Versioning

Используем [Semantic Versioning](https://semver.org/):

- `MAJOR.MINOR.PATCH`
- `MAJOR`: несовместимые изменения
- `MINOR`: новые функции (обратно совместимые)
- `PATCH`: исправления ошибок

### Release Process

1. Обновите version в package.json и pyproject.toml
2. Обновите CHANGELOG.md
3. Создайте git tag
4. Создайте GitHub Release

## 🤝 Сообщество

- Будьте вежливы и уважительны
- Помогайте новым участникам
- Следуйте Code of Conduct
- Фокусируйтесь на конструктивной критике

## 📞 Связь

- GitHub Issues: баги и feature requests
- GitHub Discussions: вопросы и обсуждения
- Email: для важных вопросов

---

Спасибо за ваш вклад! 🎉