# Разработка агентов

## Обзор агентной системы

Агентная платформа BGW позволяет создавать специализированных агентов для сбора данных из различных источников: интернет-магазинов, API, публичных Telegram каналов и других веб-ресурсов.

### Архитектура агента

```
Источник данных → Агент (fetch) → Сырые данные → Агент (parse) → События → База данных
```

## Типы агентов

### 1. HTMLAgent - Веб-скрапинг
Для статических HTML страниц с CSS селекторами.

**Применение:** интернет-магазины, каталоги, новостные сайты.

### 2. APIAgent - API интеграция
Для работы с REST API источников.

**Применение:** платформы с открытым API, JSON endpoints.

### 3. HeadlessAgent - Динамические сайты
Для сайтов с JavaScript рендерингом.

**Применение:** SPA, сайты с динамической подгрузкой.

### 4. TelegramAgent - Публичные каналы
Для мониторинга публичных Telegram каналов.

**Применение:** новостные каналы, анонсы издательств.

## Базовый интерфейс

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Fetched:
    """Полученные данные"""
    url: str
    status: int
    body: str
    headers: Dict[str, str]
    fetched_at: datetime

@dataclass
class ListingEventDraft:
    """Черновик события"""
    title: str
    url: str = None
    store_id: str = None
    kind: str = "price"  # announce|preorder|release|discount|price
    price: float = None
    discount_pct: float = None
    edition: str = None
    in_stock: bool = None
    meta: Dict[str, Any] = None

class BaseAgent(ABC):
    """Базовый класс агента"""

    TYPE: str  # 'api', 'html', 'headless', 'telegram_public'
    CONFIG_SCHEMA: Dict[str, Any] = {}  # JSON Schema

    def __init__(self, config: Dict[str, Any], secrets: Dict[str, Any], ctx: "RuntimeContext"):
        self.config = config
        self.secrets = secrets
        self.ctx = ctx

    @abstractmethod
    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение данных с учетом лимитов и robots.txt"""
        pass

    @abstractmethod
    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Извлечение событий из полученных данных"""
        pass

    async def run(self) -> AsyncGenerator[ListingEventDraft, None]:
        """Полный цикл работы агента"""
        async for fetched in self.fetch():
            async for event in self.parse(fetched):
                yield event
```

## HTMLAgent - Скрапинг HTML страниц

### Базовая реализация

```python
from bs4 import BeautifulSoup
import re
from typing import List, AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft

class StoreHTMLAgent(HTMLAgent):
    """Базовый HTML агент для магазина"""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Получаем селекторы из конфигурации
        selectors = self.config.get('selectors', {})
        item_selector = selectors.get('item', '.product-item')

        # Находим карточки товаров
        items = soup.select(item_selector)

        for item in items:
            event = await self._extract_item_data(item, selectors)
            if event:
                yield event

    async def _extract_item_data(self, item, selectors):
        """Извлечение данных из карточки товара"""
        # Заголовок
        title_elem = item.select_one(selectors.get('title', '.title'))
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)

        # URL
        url_elem = item.select_one(selectors.get('url', 'a'))
        url = url_elem.get('href') if url_elem else None

        # Цена
        price = await self._extract_price(item, selectors)

        # Определение типа события
        kind = await self._determine_event_kind(item, selectors)

        # Наличие
        in_stock = await self._extract_stock_status(item, selectors)

        return ListingEventDraft(
            title=title,
            url=self._normalize_url(url),
            price=price,
            kind=kind,
            in_stock=in_stock
        )

    async def _extract_price(self, item, selectors):
        """Извлечение цены"""
        price_elem = item.select_one(selectors.get('price', '.price'))
        if not price_elem:
            return None

        price_text = price_elem.get_text(strip=True)
        price_regex = self.config.get('price_regex', r'(\d[\d\s]*)\s*₽')

        match = re.search(price_regex, price_text)
        if match:
            price_str = match.group(1).replace(' ', '')
            try:
                return float(price_str)
            except ValueError:
                return None
        return None

    async def _determine_event_kind(self, item, selectors):
        """Определение типа события"""
        # Проверяем бейджи/метки
        badge_elem = item.select_one(selectors.get('badge', '.badge'))
        if badge_elem:
            badge_text = badge_elem.get_text(strip=True).lower()

            if any(word in badge_text for word in ['предзаказ', 'preorder']):
                return 'preorder'
            elif any(word in badge_text for word in ['новинка', 'new']):
                return 'release'
            elif any(word in badge_text for word in ['скидка', 'sale', 'discount']):
                return 'discount'

        # Анализ URL
        url = item.select_one(selectors.get('url', 'a'))
        if url:
            url_text = url.get('href', '').lower()
            if 'preorder' in url_text:
                return 'preorder'
            elif 'coming-soon' in url_text:
                return 'announce'

        return 'price'  # по умолчанию

    def _normalize_url(self, url):
        """Нормализация URL"""
        if not url:
            return None

        base_url = self.config.get('base_url')
        if base_url and not url.startswith('http'):
            return f"{base_url.rstrip('/')}/{url.lstrip('/')}"
        return url
```

### Пример конкретного агента

```python
class HobbyGamesComingSoonAgent(HTMLAgent):
    """Агент для раздела Coming Soon на Hobby Games"""

    TYPE = "html"
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "start_urls": {
                "type": "array",
                "items": {"type": "string"}
            },
            "selectors": {
                "type": "object",
                "properties": {
                    "item": {"type": "string", "default": ".product-item"},
                    "title": {"type": "string", "default": ".product-item__title"},
                    "price": {"type": "string", "default": ".product-item__price"},
                    "url": {"type": "string", "default": "a.product-item__link"},
                    "badge": {"type": "string", "default": ".product-item__label"}
                }
            },
            "price_regex": {
                "type": "string",
                "default": r"(\d[\d\s]*)\s*₽"
            },
            "base_url": {
                "type": "string",
                "default": "https://hobbygames.ru"
            }
        },
        "required": ["start_urls"]
    }

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        soup = BeautifulSoup(fetched.body, 'html.parser')

        items = soup.select(self.selectors.get('item', '.product-item'))

        for item in items:
            try:
                title = self._extract_text(item, 'title')
                if not title:
                    continue

                event = ListingEventDraft(
                    title=title,
                    url=self._extract_url(item, 'url'),
                    price=self._extract_price(item),
                    kind=self._determine_kind(item),
                    in_stock=True  # Coming Soon товары обычно доступны для предзаказа
                )

                yield event

            except Exception as e:
                self.ctx.logger.warning(f"Ошибка обработки элемента: {e}")
```

## APIAgent - Работа с API

### Пример API агента

```python
import aiohttp
import asyncio
from typing import AsyncGenerator
from ..base import BaseAgent, Fetched, ListingEventDraft

class StoreAPIAgent(BaseAgent):
    """Агент для работы с API магазина"""

    TYPE = "api"
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "api_base_url": {"type": "string"},
            "api_key": {"type": "string"},
            "endpoints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "method": {"type": "string", "enum": ["GET", "POST"]},
                        "params": {"type": "object"},
                        "headers": {"type": "object"}
                    }
                }
            },
            "rate_limit": {
                "type": "object",
                "properties": {
                    "rps": {"type": "number"},
                    "requests_per_minute": {"type": "integer"}
                }
            }
        },
        "required": ["api_base_url", "endpoints"]
    }

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение данных из API"""
        headers = {
            'Authorization': f"Bearer {self.secrets.get('api_key')}",
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            for endpoint in self.config['endpoints']:
                url = f"{self.config['api_base_url']}/{endpoint['path'].lstrip('/')}"

                # Учет rate limiting
                await self._wait_for_rate_limit()

                try:
                    async with session.request(
                        method=endpoint.get('method', 'GET'),
                        url=url,
                        params=endpoint.get('params'),
                        headers=endpoint.get('headers')
                    ) as response:
                        if response.status == 200:
                            data = await response.text()

                            yield Fetched(
                                url=url,
                                status=response.status,
                                body=data,
                                headers=dict(response.headers),
                                fetched_at=datetime.now()
                            )
                        else:
                            self.ctx.logger.error(f"API ошибка: {response.status}")

                except Exception as e:
                    self.ctx.logger.error(f"Ошибка запроса к API: {e}")

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Парсинг JSON ответа от API"""
        try:
            data = json.loads(fetched.body)

            # Обработка разных форматов ответа
            if isinstance(data, dict):
                if 'products' in data:
                    products = data['products']
                elif 'items' in data:
                    products = data['items']
                elif 'data' in data:
                    products = data['data']
                else:
                    products = [data]
            elif isinstance(data, list):
                products = data
            else:
                return

            for product in products:
                event = self._extract_product_data(product)
                if event:
                    yield event

        except json.JSONDecodeError as e:
            self.ctx.logger.error(f"Ошибка парсинга JSON: {e}")

    def _extract_product_data(self, product):
        """Извлечение данных о продукте"""
        title = product.get('title') or product.get('name')
        if not title:
            return None

        return ListingEventDraft(
            title=title,
            url=product.get('url') or product.get('link'),
            price=product.get('price'),
            discount_pct=product.get('discount_percentage'),
            in_stock=product.get('in_stock', product.get('available', True)),
            kind=self._determine_kind(product),
            meta={
                'api_id': product.get('id'),
                'category': product.get('category'),
                'brand': product.get('brand')
            }
        )
```

## HeadlessAgent - Динамические сайты

### Пример с Playwright

```python
from playwright.async_api import async_playwright
from ..base import BaseAgent, Fetched, ListingEventDraft

class StoreHeadlessAgent(BaseAgent):
    """Агент для динамических сайтов с Playwright"""

    TYPE = "headless"
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "urls": {"type": "array", "items": {"type": "string"}},
            "wait_for_selector": {"type": "string"},
            "scroll_to_load": {"type": "boolean", "default": false},
            "screenshot": {"type": "boolean", "default": false},
            "timeout": {"type": "integer", "default": 30000}
        }
    }

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Загрузка страниц через Playwright"""

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for url in self.config['urls']:
                try:
                    page = await browser.new_page()

                    # Настройка user-agent и viewport
                    await page.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    await page.set_viewport_size({"width": 1920, "height": 1080})

                    # Навигация
                    await page.goto(url, wait_until='networkidle')

                    # Ожидание селектора
                    wait_selector = self.config.get('wait_for_selector')
                    if wait_selector:
                        await page.wait_for_selector(wait_selector, timeout=self.config.get('timeout', 30000))

                    # Прокрутка для подгрузки контента
                    if self.config.get('scroll_to_load'):
                        await self._scroll_to_load(page)

                    # Получение HTML
                    content = await page.content()

                    # Скриншот для отладки
                    if self.config.get('screenshot'):
                        await page.screenshot(path=f"debug_{url.replace('/', '_')}.png")

                    yield Fetched(
                        url=url,
                        status=200,
                        body=content,
                        headers={},
                        fetched_at=datetime.now()
                    )

                    await page.close()

                except Exception as e:
                    self.ctx.logger.error(f"Ошибка загрузки страницы {url}: {e}")

            await browser.close()

    async def _scroll_to_load(self, page):
        """Прокрутка для динамической подгрузки контента"""
        last_height = await page.evaluate("document.body.scrollHeight")

        while True:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)  # ожидание загрузки

            new_height = await page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
```

## TelegramAgent - Публичные каналы

```python
import aiohttp
from bs4 import BeautifulSoup
from ..base import BaseAgent, Fetched, ListingEventDraft

class TelegramChannelAgent(BaseAgent):
    """Агент для публичных Telegram каналов"""

    TYPE = "telegram_public"
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "channel_username": {"type": "string"},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "max_posts": {"type": "integer", "default": 50}
        },
        "required": ["channel_username"]
    }

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение постов из публичного канала"""
        channel = self.config['channel_username'].lstrip('@')
        url = f"https://t.me/s/{channel}"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()

                        yield Fetched(
                            url=url,
                            status=response.status,
                            body=content,
                            headers=dict(response.headers),
                            fetched_at=datetime.now()
                        )
                    else:
                        self.ctx.logger.error(f"Ошибка загрузки канала: {response.status}")

            except Exception as e:
                self.ctx.logger.error(f"Ошибка запроса к Telegram: {e}")

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Парсинг постов канала"""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Находим посты
        posts = soup.select('.tgme_widget_message')

        keywords = [kw.lower() for kw in self.config.get('keywords', [])]
        max_posts = self.config.get('max_posts', 50)

        for i, post in enumerate(posts[:max_posts]):
            try:
                text_elem = post.select_one('.tgme_widget_message_text')
                if not text_elem:
                    continue

                text = text_elem.get_text(strip=True).lower()

                # Проверяем ключевые слова
                if keywords and not any(kw in text for kw in keywords):
                    continue

                # Извлекаем ссылку
                link_elem = post.select_one('a[href*="t.me"]')
                url = link_elem.get('href') if link_elem else fetched.url

                # Определяем тип события по тексту
                kind = self._determine_kind_from_text(text)

                yield ListingEventDraft(
                    title=text[:200],  # обрезаем длинные тексты
                    url=url,
                    kind=kind,
                    meta={
                        'source': 'telegram',
                        'channel': self.config['channel_username'],
                        'message_id': post.get('data-post')
                    }
                )

            except Exception as e:
                self.ctx.logger.warning(f"Ошибка обработки поста: {e}")

    def _determine_kind_from_text(self, text):
        """Определение типа события по тексту"""
        if any(word in text for word in ['предзаказ', 'preorder', 'скоро']):
            return 'preorder'
        elif any(word in text for word in ['релиз', 'вышел', 'в продаже']):
            return 'release'
        elif any(word in text for word in ['анонс', 'announce']):
            return 'announce'
        elif any(word in text for word in ['скидка', 'sale', 'discount']):
            return 'discount'

        return 'announce'  # по умолчанию
```

## Манифест агента

Каждый агент поставляется с JSON манифестом:

```json
{
  "version": "1.0",
  "id": "hobbygames_coming_soon",
  "name": "Hobby Games — Coming Soon",
  "description": "Мониторинг раздела предзаказов Hobby Games",
  "type": "html",
  "entrypoint": "agent.py",
  "author": "BGW Team",
  "created_at": "2024-01-01T00:00:00Z",
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
      "badge": ".product-item__label"
    },
    "price_regex": "([0-9][0-9\\s]+)\\s*₽"
  },
  "secrets": {
    "api_key": {
      "description": "API ключ для доступа",
      "required": false
    }
  },
  "tags": ["boardgames", "shop", "preorder"],
  "language": "ru",
  "region": "RU"
}
```

## Тестирование агентов

### Unit тесты

```python
import pytest
from unittest.mock import Mock, AsyncMock
from app.agents.builtin.hobbygames import HobbyGamesComingSoonAgent

@pytest.mark.asyncio
async def test_hobbygames_agent():
    # Мок контекста
    mock_ctx = Mock()
    mock_ctx.logger = Mock()

    # Конфигурация агента
    config = {
        'start_urls': ['https://hobbygames.ru/coming-soon'],
        'selectors': {
            'item': '.product-item',
            'title': '.product-item__title',
            'price': '.product-item__price'
        },
        'base_url': 'https://hobbygames.ru'
    }

    agent = HobbyGamesComingSoonAgent(config, {}, mock_ctx)

    # Тестовый HTML
    test_html = """
    <div class="product-item">
        <div class="product-item__title">Тестовая игра</div>
        <div class="product-item__price">2 500 ₽</div>
        <a class="product-item__link" href="/test-game"></a>
    </div>
    """

    fetched = Fetched(
        url='https://hobbygames.ru/coming-soon',
        status=200,
        body=test_html,
        headers={},
        fetched_at=datetime.now()
    )

    # Тестирование парсинга
    events = []
    async for event in agent.parse(fetched):
        events.append(event)

    assert len(events) == 1
    assert events[0].title == 'Тестовая игра'
    assert events[0].price == 2500.0
    assert events[0].url == 'https://hobbygames.ru/test-game'
```

### Интеграционные тесты

```python
import pytest
import aiohttp
from app.agents.builtin.hobbygames import HobbyGamesComingSoonAgent

@pytest.mark.asyncio
async def test_agent_integration():
    config = {
        'start_urls': ['https://hobbygames.ru/coming-soon'],
        'selectors': {...}
    }

    agent = HobbyGamesComingSoonAgent(config, {}, Mock())

    # Запуск агента
    events = []
    async for event in agent.run():
        events.append(event)
        if len(events) >= 5:  # ограничиваем для теста
            break

    assert len(events) > 0
    assert all(event.title for event in events)
```

## Логирование и отладка

```python
import logging
from typing import Dict, Any

class RuntimeContext:
    def __init__(self, agent_id: str, logger: logging.Logger):
        self.agent_id = agent_id
        self.logger = logger
        self.stats = {
            'pages_fetched': 0,
            'events_created': 0,
            'errors': 0
        }

    def increment_stat(self, key: str, value: int = 1):
        self.stats[key] = self.stats.get(key, 0) + value

    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()
```

## Рекомендации по разработке

### 1. Обработка ошибок
```python
async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
    try:
        # Основная логика
        pass
    except Exception as e:
        self.ctx.logger.error(f"Ошибка парсинга {fetched.url}: {e}")
        self.ctx.increment_stat('errors')
        # Не прерываем выполнение, продолжаем с другими элементами
```

### 2. Учет rate limiting
```python
import asyncio
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, rps: float, burst: int):
        self.rps = rps
        self.burst = burst
        self.tokens = burst
        self.last_refill = datetime.now()

    async def acquire(self):
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()

        # Пополнение токенов
        self.tokens = min(self.burst, self.tokens + elapsed * self.rps)
        self.last_refill = now

        if self.tokens < 1:
            wait_time = (1 - self.tokens) / self.rps
            await asyncio.sleep(wait_time)
            self.tokens = 0
        else:
            self.tokens -= 1
```

### 3. Валидация данных
```python
def validate_event(event: ListingEventDraft) -> bool:
    """Валидация события"""
    if not event.title or len(event.title.strip()) < 3:
        return False

    if event.price is not None and (event.price < 0 or event.price > 100000):
        return False

    if event.discount_pct is not None and (event.discount_pct < 0 or event.discount_pct > 100):
        return False

    return True
```

### 4. Кэширование результатов
```python
import hashlib

def get_content_hash(content: str) -> str:
    """Получение хеша контента для дедупликации"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]

# В агенте
async def fetch(self) -> AsyncGenerator[Fetched, None]:
    for url in self.config['start_urls']:
        content = await self._fetch_content(url)
        content_hash = get_content_hash(content)

        # Проверяем, не обрабатывали ли ранее
        if await self._is_content_processed(content_hash):
            continue

        yield Fetched(...)
        await self._mark_content_processed(content_hash)
```

## Деплоймент агентов

### Упаковка в ZIP

```bash
# Создание ZIP архива агента
zip -r hobbygames_agent.zip \
    manifest.json \
    agent.py \
    requirements.txt

# Импорт через API
curl -X POST "http://localhost:8000/agents/import" \
  -H "Authorization: Bearer <token>" \
  -F "file=@hobbygames_agent.zip"
```

### Конфигурация в production

```python
# Перекрытие конфигурации для production
production_config = {
    **development_config,
    'rate_limit': {
        'rps': 0.1,  # более консервативные лимиты
        'daily_pages_cap': 30
    },
    'timeout': 30,
    'retry_attempts': 3
}
```

Эта документация предоставляет полную информацию для разработки и тестирования агентов в системе BGW.