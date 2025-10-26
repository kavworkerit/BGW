# Руководство по разработке агентов BGW

## Обзор

Агенты - это модули, которые собирают данные из различных источников (интернет-магазины, публикации, API) и преобразуют их в стандартизированные события в системе BGW.

## Архитектура агентов

### Базовые классы

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import aiohttp
import asyncio

@dataclass
class Fetched:
    """Результат получения данных."""
    url: str
    status: int
    body: str
    headers: Dict[str, str]
    fetched_at: datetime

@dataclass
class ListingEventDraft:
    """Черновик события листинга."""
    title: str
    store_id: str
    url: str
    kind: str = "announce"  # announce, preorder, release, discount, price
    price: float = None
    discount_pct: float = None
    edition: str = None
    in_stock: bool = None
    source_id: str = None

class BaseAgent(ABC):
    """Базовый класс для всех агентов."""

    TYPE = "base"  # html, api, headless, telegram_public
    CONFIG_SCHEMA = {}  # JSON Schema для валидации

    def __init__(self, config: Dict[str, Any], secrets: Dict[str, Any], ctx: "RuntimeContext"):
        self.config = config
        self.secrets = secrets
        self.ctx = ctx
        self.session = ctx.session

    @abstractmethod
    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение данных из источника."""
        pass

    @abstractmethod
    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Парсинг полученных данных."""
        pass

    async def run(self) -> AsyncGenerator[ListingEventDraft, None]:
        """Основной метод выполнения агента."""
        async for fetched in self.fetch():
            async for event in self.parse(fetched):
                yield event
```

### Runtime Context

```python
class RuntimeContext:
    """Контекст выполнения агента."""

    def __init__(self, session: aiohttp.ClientSession, rate_limiter, storage):
        self.session = session
        self.rate_limiter = rate_limiter
        self.storage = storage
        self.logger = logging.getLogger(f"agent.{self.__class__.__name__}")

    async def get(self, url: str, **kwargs) -> Fetched:
        """Выполнить GET запрос с учетом лимитов."""
        await self.rate_limiter.wait()

        async with self.session.get(url, **kwargs) as response:
            return Fetched(
                url=url,
                status=response.status,
                body=await response.text(),
                headers=dict(response.headers),
                fetched_at=datetime.now()
            )

    async def store_raw(self, content: str, url: str) -> str:
        """Сохранить сырые данные в S3."""
        return await self.storage.store(content, url)
```

## Типы агентов

### 1. HTMLAgent - Парсинг HTML страниц

Для статических сайтов с доступом к HTML.

```python
from bs4 import BeautifulSoup
import re

class HTMLAgent(BaseAgent):
    """Агент для парсинга HTML страниц."""

    TYPE = "html"

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение HTML страниц."""
        start_urls = self.config.get('start_urls', [])

        for url in start_urls:
            fetched = await self.ctx.get(url)
            yield fetched

            # Обработка пагинации
            async for next_page in self._find_pagination(fetched):
                next_fetched = await self.ctx.get(next_page)
                yield next_fetched

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Парсинг HTML и извлечение данных."""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        items = soup.select(self.config['selectors']['item'])

        for item in items:
            title = self._extract_text(item, 'title')
            price = self._extract_price(item)
            url = self._extract_url(item)
            kind = self._detect_kind(item)

            if title:
                yield ListingEventDraft(
                    title=title,
                    store_id=self.config['store_id'],
                    url=url,
                    kind=kind,
                    price=price,
                    source_id=self.ctx.agent_id
                )

    def _extract_text(self, element, selector: str) -> str:
        """Извлечение текста по селектору."""
        el = element.select_one(selector)
        return el.get_text(strip=True) if el else ""

    def _extract_price(self, item) -> float:
        """Извлечение цены."""
        price_text = self._extract_text(item, 'price')
        if not price_text:
            return None

        # Удаляем все символы кроме цифр и точки
        price_match = re.search(r'[\d,\.]+', price_text.replace(' ', ''))
        if price_match:
            try:
                return float(price_match.group().replace(',', '.'))
            except ValueError:
                return None
        return None

    def _extract_url(self, item) -> str:
        """Извлечение URL."""
        link = item.select_one(self.config['selectors'].get('url', 'a'))
        if link:
            href = link.get('href')
            if href:
                return self._resolve_url(href, self.ctx.current_url)
        return ""

    def _detect_kind(self, item) -> str:
        """Определение типа события."""
        # Проверяем наличие индикаторов скидки
        if self._extract_text(item, 'badge'):
            badge_text = self._extract_text(item, 'badge').lower()
            if 'скидка' in badge_text or 'sale' in badge_text:
                return 'discount'
            elif 'новинка' in badge_text or 'new' in badge_text:
                return 'release'
            elif 'предзаказ' in badge_text or 'preorder' in badge_text:
                return 'preorder'

        return 'announce'
```

### 2. APIAgent - Работа с REST API

Для источников с официальным API.

```python
import json

class APIAgent(BaseAgent):
    """Агент для работы с REST API."""

    TYPE = "api"

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение данных через API."""
        api_base = self.config['api_base_url']
        endpoints = self.config.get('endpoints', ['products'])

        for endpoint in endpoints:
            url = f"{api_base}/{endpoint}"

            # Добавляем параметры запроса
            params = self.config.get('params', {})
            headers = {
                'Authorization': f"Bearer {self.secrets.get('api_key')}",
                'Content-Type': 'application/json'
            }

            fetched = await self.ctx.get(url, params=params, headers=headers)
            yield fetched

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Парсинг JSON ответа API."""
        try:
            data = json.loads(fetched.body)

            # Обработка разных форматов ответа
            items = data
            if 'data' in data:
                items = data['data']
            elif 'results' in data:
                items = data['results']

            for item in items:
                event = ListingEventDraft(
                    title=item.get('title', ''),
                    store_id=self.config['store_id'],
                    url=item.get('url', ''),
                    kind=self._map_api_kind(item.get('type')),
                    price=item.get('price'),
                    discount_pct=item.get('discount_percentage'),
                    edition=item.get('edition'),
                    in_stock=item.get('in_stock', True),
                    source_id=self.ctx.agent_id
                )

                if event.title:
                    yield event

        except json.JSONDecodeError as e:
            self.ctx.logger.error(f"Failed to parse JSON: {e}")

    def _map_api_kind(self, api_type: str) -> str:
        """Маппинг типов из API в нашу систему."""
        mapping = {
            'new': 'release',
            'preorder': 'preorder',
            'sale': 'discount',
            'announcement': 'announce'
        }
        return mapping.get(api_type.lower(), 'announce')
```

### 3. HeadlessAgent - Парсинг динамических сайтов

Для сайтов, требующих JavaScript.

```python
from playwright.async_api import async_playwright

class HeadlessAgent(BaseAgent):
    """Агент для парсинга динамических сайтов."""

    TYPE = "headless"

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение данных через Playwright."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Настройка user agent
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            for url in self.config['start_urls']:
                # Ожидание загрузки страницы
                await page.goto(url, wait_until='networkidle')

                # Ожидание специфических элементов
                await page.wait_for_selector(self.config['selectors']['item'], timeout=10000)

                # Скроллинг для ленивой загрузки
                await self._scroll_for_lazy_load(page)

                # Получаем HTML
                content = await page.content()

                yield Fetched(
                    url=url,
                    status=200,
                    body=content,
                    headers={},
                    fetched_at=datetime.now()
                )

            await browser.close()

    async def _scroll_for_lazy_load(self, page):
        """Скроллинг для загрузки всего контента."""
        last_height = await page.evaluate("document.body.scrollHeight")

        while True:
            # Скроллим вниз
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")

            # Ждем загрузки
            await asyncio.sleep(2)

            # Проверяем, есть ли новый контент
            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
```

## Конфигурация агентов

### Структура манифеста

```json
{
  "version": "1.0",
  "id": "hobbygames_coming_soon",
  "name": "Hobby Games — Coming Soon",
  "type": "html",
  "entrypoint": "agent.py",
  "schedule": {
    "cron": "0 */2 * * *",
    "timezone": "Europe/Moscow"
  },
  "rate_limit": {
    "rps": 0.3,
    "burst": 1,
    "daily_pages_cap": 50
  },
  "config": {
    "store_id": "hobbygames",
    "start_urls": ["https://hobbygames.ru/coming-soon"],
    "selectors": {
      "item": ".product-item",
      "title": ".product-item__title",
      "price": ".product-item__price",
      "url": ".product-item__link::attr(href)",
      "badge": ".product-item__label"
    },
    "price_regex": "([0-9][0-9\\s]+)\\s*₽"
  },
  "secrets": {}
}
```

### Rate Limiting

```python
class RateLimiter:
    """Контроль скорости запросов."""

    def __init__(self, rps: float, burst: int, daily_cap: int):
        self.rps = rps
        self.burst = burst
        self.daily_cap = daily_cap
        self.tokens = burst
        self.last_refill = time.time()
        self.daily_used = 0
        self.last_reset = datetime.now().date()

    async def wait(self):
        """Ожидание следующего разрешенного запроса."""
        # Проверяем дневной лимит
        if date.today() > self.last_reset:
            self.daily_used = 0
            self.last_reset = date.today()

        if self.daily_used >= self.daily_cap:
            raise Exception("Daily rate limit exceeded")

        # Ждем пополнения токенов
        while self.tokens < 1:
            await asyncio.sleep(0.1)
            self._refill_tokens()

        self.tokens -= 1
        self.daily_used += 1
```

## Тестирование агентов

### Unit тесты

```python
import pytest
from unittest.mock import Mock, AsyncMock

@pytest.mark.asyncio
async def test_html_agent_parsing():
    """Тест парсинга HTML."""
    agent = HTMLAgent(config, {}, mock_ctx)

    html_content = """
    <div class="product-item">
        <h3 class="product-item__title">Dune: Imperium</h3>
        <div class="product-item__price">2 999 ₽</div>
        <a class="product-item__link" href="/product/123"></a>
    </div>
    """

    fetched = Fetched(
        url="http://example.com",
        status=200,
        body=html_content,
        headers={},
        fetched_at=datetime.now()
    )

    events = [event async for event in agent.parse(fetched)]

    assert len(events) == 1
    assert events[0].title == "Dune: Imperium"
    assert events[0].price == 2999.0

@pytest.mark.asyncio
async def test_agent_rate_limiting():
    """Тест ограничения скорости."""
    rate_limiter = RateLimiter(rps=1.0, burst=5, daily_cap=100)

    start_time = time.time()

    # Делаем 3 запроса
    for _ in range(3):
        await rate_limiter.wait()

    elapsed = time.time() - start_time
    assert elapsed >= 2.0  # Должно занять не менее 2 секунд
```

### Integration тесты

```python
@pytest.mark.integration
async def test_agent_full_run():
    """Интеграционный тест полного выполнения агента."""
    agent = HTMLAgent(config, secrets, real_context)

    events = []
    async for event in agent.run():
        events.append(event)

    assert len(events) > 0
    assert all(event.title for event in events)
    assert all(event.store_id for event in events)
```

## Отладка и мониторинг

### Логирование

```python
import logging

logger = logging.getLogger(f"agent.{self.__class__.__name__}")

async def fetch(self):
    logger.info(f"Starting fetch from {self.config['start_urls']}")

    try:
        fetched = await self.ctx.get(url)
        logger.debug(f"Successfully fetched {url}, status: {fetched.status}")
        yield fetched
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        raise
```

### Метрики

```python
from prometheus_client import Counter, Histogram

# Метрики для агента
AGENT_RUNS_TOTAL = Counter('agent_runs_total', 'Total agent runs', ['agent_id', 'status'])
FETCH_DURATION = Histogram('agent_fetch_duration_seconds', 'Fetch duration', ['agent_id'])
PARSE_DURATION = Histogram('agent_parse_duration_seconds', 'Parse duration', ['agent_id'])

async def run(self):
    start_time = time.time()

    try:
        async for event in self.fetch():
            AGENT_RUNS_TOTAL.labels(agent_id=self.ctx.agent_id, status='success').inc()
            yield event
    except Exception as e:
        AGENT_RUNS_TOTAL.labels(agent_id=self.ctx.agent_id, status='error').inc()
        raise
    finally:
        duration = time.time() - start_time
        FETCH_DURATION.labels(agent_id=self.ctx.agent_id).observe(duration)
```

## Лучшие практики

### 1. Обработка ошибок

```python
async def fetch(self):
    retries = 3

    for url in self.config['start_urls']:
        for attempt in range(retries):
            try:
                fetched = await self.ctx.get(url)
                yield fetched
                break
            except Exception as e:
                if attempt == retries - 1:
                    self.ctx.logger.error(f"Failed after {retries} attempts: {e}")
                    raise
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### 2. Валидация данных

```python
def validate_event(event: ListingEventDraft) -> bool:
    """Валидация события."""
    if not event.title or len(event.title.strip()) < 3:
        return False

    if event.price and (event.price < 0 or event.price > 100000):
        return False

    if not event.store_id:
        return False

    return True

async def parse(self, fetched: Fetched):
    # ... парсинг ...

    for raw_event in raw_events:
        if self.validate_event(raw_event):
            yield raw_event
```

### 3. Кэширование

```python
class CachedAgent(BaseAgent):
    """Агент с поддержкой кэширования."""

    def __init__(self, config, secrets, ctx):
        super().__init__(config, secrets, ctx)
        self.cache = ctx.cache

    async def fetch(self):
        for url in self.config['start_urls']:
            cache_key = f"agent:{self.ctx.agent_id}:{hashlib.md5(url.encode()).hexdigest()}"

            # Проверяем кэш
            cached = await self.cache.get(cache_key)
            if cached:
                yield Fetched.from_cached(cached)
                continue

            # Получаем свежие данные
            fetched = await self.ctx.get(url)

            # Сохраняем в кэш на 1 час
            await self.cache.set(cache_key, fetched.to_dict(), ttl=3600)
            yield fetched
```

### 4. Конфигурация через переменные окружения

```python
class ConfigurableAgent(BaseAgent):
    """Агент с конфигурацией через env."""

    def __init__(self, config, secrets, ctx):
        super().__init__(config, secrets, ctx)

        # Читаем чувствительные данные из env
        self.api_key = os.getenv('AGENT_API_KEY') or secrets.get('api_key')
        self.base_url = os.getenv('AGENT_BASE_URL') or config.get('base_url')

        if not self.api_key:
            raise ValueError("API key is required")
```

## Деплоймент агентов

### Регистрация агента

```python
from app.agents.registry import agent_registry

@agent_registry.register("hobbygames_coming_soon")
class HobbyGamesAgent(HTMLAgent):
    """Агент для Hobby Games."""
    pass
```

### Запуск через Celery

```python
from celery import Celery
from app.agents.loader import load_agent

celery_app = Celery('bgw_agents')

@celery_app.task
def run_agent(agent_id: str):
    """Запуск агента через Celery."""
    agent = load_agent(agent_id)

    async def execute():
        events = []
        async for event in agent.run():
            events.append(event)
        return events

    return asyncio.run(execute())
```