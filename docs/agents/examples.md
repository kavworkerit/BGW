# 📦 Примеры агентов

В этом разделе собраны готовые примеры агентов для разных типов источников данных. Вы можете использовать их как основу для создания собственных агентов.

## 🏪 Агенты для интернет-магазинов

### Пример 1: Магазин с простыми карточками товаров

**Источник:** Магазин с стандартной структурой карточек

```python
# simple_store_agent.py
from bs4 import BeautifulSoup
import re
from typing import AsyncGenerator
from ..base import HTMLAgent, Fetched, ListingEventDraft

class SimpleStoreAgent(HTMLAgent):
    """Агент для магазинов с простой структурой карточек"""

    TYPE = "html"
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "start_urls": {"type": "array", "items": {"type": "string"}},
            "base_url": {"type": "string"},
            "selectors": {
                "type": "object",
                "properties": {
                    "item": {"type": "string", "default": ".product"},
                    "title": {"type": "string", "default": ".title"},
                    "price": {"type": "string", "default": ".price"},
                    "url": {"type": "string", "default": "a"},
                    "availability": {"type": "string", "default": ".stock"},
                    "badge": {"type": "string", "default": ".badge"}
                }
            },
            "price_regex": {"type": "string", "default": r"(\d[\d\s]*)\s*₽"}
        },
        "required": ["start_urls"]
    }

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        soup = BeautifulSoup(fetched.body, 'html.parser')
        selectors = self.config.get('selectors', {})

        items = soup.select(selectors.get('item', '.product'))

        for item in items:
            try:
                event = await self._extract_event(item, selectors)
                if event:
                    yield event
            except Exception as e:
                self.ctx.logger.warning(f"Ошибка обработки элемента: {e}")

    async def _extract_event(self, item, selectors):
        # Заголовок
        title_elem = item.select_one(selectors.get('title', '.title'))
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)

        # URL
        url_elem = item.select_one(selectors.get('url', 'a'))
        url = self._normalize_url(url_elem.get('href') if url_elem else None)

        # Цена
        price = await self._extract_price(item, selectors)

        # Тип события
        kind = await self._determine_event_kind(item, selectors)

        # Наличие
        in_stock = await self._check_availability(item, selectors)

        return ListingEventDraft(
            title=title,
            url=url,
            price=price,
            kind=kind,
            in_stock=in_stock
        )

    async def _extract_price(self, item, selectors):
        price_elem = item.select_one(selectors.get('price', '.price'))
        if not price_elem:
            return None

        price_text = price_elem.get_text(strip=True)
        price_regex = self.config.get('price_regex', r"(\d[\d\s]*)\s*₽")

        match = re.search(price_regex, price_text)
        if match:
            price_str = match.group(1).replace(' ', '')
            try:
                return float(price_str)
            except ValueError:
                return None
        return None

    async def _determine_event_kind(self, item, selectors):
        # Проверяем бейджи
        badge_elem = item.select_one(selectors.get('badge', '.badge'))
        if badge_elem:
            badge_text = badge_elem.get_text(strip=True).lower()
            if any(word in badge_text for word in ['предзаказ', 'preorder']):
                return 'preorder'
            elif any(word in badge_text for word in ['новинка', 'new']):
                return 'release'
            elif any(word in badge_text for word in ['скидка', 'sale']):
                return 'discount'

        return 'price'

    async def _check_availability(self, item, selectors):
        stock_elem = item.select_one(selectors.get('availability', '.stock'))
        if stock_elem:
            stock_text = stock_elem.get_text(strip=True).lower()
            return any(word in stock_text for word in ['в наличии', 'available', 'купить'])
        return True  # По умолчанию считаем что в наличии

    def _normalize_url(self, url):
        if not url:
            return None

        base_url = self.config.get('base_url')
        if base_url and not url.startswith('http'):
            return f"{base_url.rstrip('/')}/{url.lstrip('/')}"
        return url
```

**Манифест:**
```json
{
  "version": "1.0",
  "id": "simple_store_agent",
  "name": "Simple Store Agent",
  "description": "Базовый агент для магазинов с простой структурой",
  "type": "html",
  "entrypoint": "agent.py",
  "schedule": {
    "cron": "0 */4 * * *",
    "timezone": "Europe/Moscow"
  },
  "rate_limit": {
    "rps": 0.5,
    "burst": 1,
    "daily_pages_cap": 100
  },
  "config": {
    "start_urls": ["https://example-store.com/catalog"],
    "base_url": "https://example-store.com",
    "selectors": {
      "item": ".product-card",
      "title": ".product-title",
      "price": ".price-current",
      "url": ".product-link",
      "availability": ".stock-status"
    },
    "price_regex": "([0-9][0-9\\s]+)\\s*₽"
  }
}
```

### Пример 2: Магазин с пагинацией

```python
# paginated_store_agent.py
from ..base import HTMLAgent, Fetched, ListingEventDraft
from urllib.parse import urljoin, urlparse, parse_qs

class PaginatedStoreAgent(HTMLAgent):
    """Агент для магазинов с пагинацией"""

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        base_url = self.config['start_urls'][0]
        page = 1
        max_pages = self.config.get('max_pages', 10)

        while page <= max_pages:
            # Формируем URL страницы
            page_url = self._build_page_url(base_url, page)

            # Получаем страницу
            fetched = await self._fetch_page(page_url)
            if not fetched:
                break

            yield fetched

            # Проверяем есть ли следующая страница
            if not await self._has_next_page(fetched):
                break

            page += 1

    def _build_page_url(self, base_url, page):
        """Строит URL для конкретной страницы"""
        if '?' in base_url:
            return f"{base_url}&page={page}"
        else:
            return f"{base_url}?page={page}"

    async def _has_next_page(self, fetched):
        """Проверяет есть ли следующая страница"""
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем кнопку "Следующая страница"
        next_btn = soup.select_one('.pagination .next:not(.disabled)')
        if next_btn:
            return True

        # Или проверяем номер текущей страницы
        current_page_elem = soup.select_one('.pagination .current')
        if current_page_elem:
            try:
                current_page = int(current_page_elem.get_text(strip=True))
                total_pages_elem = soup.select_one('.pagination .total')
                if total_pages_elem:
                    total_pages = int(total_pages_elem.get_text(strip=True))
                    return current_page < total_pages
            except ValueError:
                pass

        return False
```

## 📰 Агенты для новостных сайтов и блогов

### Пример 3: Блог с новостями об играх

```python
# blog_news_agent.py
from datetime import datetime
from ..base import HTMLAgent, Fetched, ListingEventDraft

class BlogNewsAgent(HTMLAgent):
    """Агент для блогов с новостями об играх"""

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем статьи
        articles = soup.select(self.config.get('article_selector', '.article'))

        for article in articles:
            event = await self._extract_article_event(article)
            if event:
                yield event

    async def _extract_article_event(self, article):
        # Заголовок статьи
        title_elem = article.select_one(self.config.get('title_selector', 'h2'))
        if not title_elem:
            return None

        title = title_elem.get_text(strip=True)

        # URL статьи
        link_elem = article.select_one('a')
        url = self._normalize_url(link_elem.get('href') if link_elem else None)

        # Дата публикации
        date_elem = article.select_one(self.config.get('date_selector', '.date'))
        published_at = await self._parse_date(date_elem) if date_elem else None

        # Извлекаем информацию об играх из текста
        games_mentioned = await self._extract_games_from_article(article)

        if games_mentioned:
            return ListingEventDraft(
                title=title,
                url=url,
                kind='announce',
                meta={
                    'published_at': published_at,
                    'games_mentioned': games_mentioned,
                    'source_type': 'blog_news'
                }
            )

        return None

    async def _parse_date(self, date_elem):
        """Парсит дату из элемента"""
        date_text = date_elem.get_text(strip=True)

        # Примеры форматов: "01.01.2024", "1 января 2024"
        date_patterns = [
            r'(\d{2})\.(\d{2})\.(\d{4})',  # DD.MM.YYYY
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',  # D Month YYYY
        ]

        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                # Конвертация в datetime
                return datetime.strptime(date_text, '%Y-%m-%d')

        return None

    async def _extract_games_from_article(self, article):
        """Извлекает названия игр из текста статьи"""
        text = article.get_text()

        # Список известных игр (можно расширять)
        known_games = self.config.get('known_games', [])
        found_games = []

        for game in known_games:
            if game.lower() in text.lower():
                found_games.append(game)

        return found_games
```

## 🤖 Агенты для API

### Пример 4: REST API магазина

```python
# api_store_agent.py
import aiohttp
import json
from ..base import BaseAgent, Fetched, ListingEventDraft

class APIStoreAgent(BaseAgent):
    """Агент для работы с REST API магазинов"""

    TYPE = "api"
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "api_base_url": {"type": "string"},
            "endpoints": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "method": {"type": "string", "enum": ["GET", "POST"]},
                        "params": {"type": "object"}
                    }
                }
            },
            "headers": {"type": "object"},
            "rate_limit": {
                "type": "object",
                "properties": {
                    "requests_per_minute": {"type": "integer", "default": 30}
                }
            }
        },
        "required": ["api_base_url", "endpoints"]
    }

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        headers = self.config.get('headers', {})
        headers.update({
            'User-Agent': 'BGW-Agent/1.0',
            'Accept': 'application/json'
        })

        async with aiohttp.ClientSession(headers=headers) as session:
            for endpoint in self.config['endpoints']:
                url = f"{self.config['api_base_url']}/{endpoint['path'].lstrip('/')}"

                # Учет rate limiting
                await self._wait_for_rate_limit()

                try:
                    async with session.request(
                        method=endpoint.get('method', 'GET'),
                        url=url,
                        params=endpoint.get('params')
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
                            self.ctx.logger.error(f"API ошибка: {response.status} для {url}")

                except Exception as e:
                    self.ctx.logger.error(f"Ошибка запроса к API {url}: {e}")

    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        try:
            data = json.loads(fetched.body)

            # Обработка разных форматов ответа
            products = self._extract_products_from_response(data)

            for product in products:
                event = self._create_event_from_product(product)
                if event:
                    yield event

        except json.JSONDecodeError as e:
            self.ctx.logger.error(f"Ошибка парсинга JSON: {e}")

    def _extract_products_from_response(self, data):
        """Извлекает продукты из API ответа"""
        if isinstance(data, dict):
            # Разные структуры ответа
            return (
                data.get('products') or
                data.get('items') or
                data.get('data') or
                [data]  # Если один продукт
            )
        elif isinstance(data, list):
            return data
        return []

    def _create_event_from_product(self, product):
        """Создает событие из данных продукта"""
        title = product.get('title') or product.get('name')
        if not title:
            return None

        return ListingEventDraft(
            title=title,
            url=product.get('url') or product.get('link'),
            price=product.get('price'),
            discount_pct=product.get('discount_percentage'),
            in_stock=product.get('in_stock', True),
            kind=self._determine_kind(product),
            meta={
                'api_id': product.get('id'),
                'category': product.get('category'),
                'brand': product.get('brand'),
                'source': 'api'
            }
        )

    def _determine_kind(self, product):
        """Определяет тип события"""
        if product.get('preorder'):
            return 'preorder'
        elif product.get('sale') or product.get('discount'):
            return 'discount'
        elif product.get('new'):
            return 'release'
        return 'price'
```

## 📱 Агенты для Telegram

### Пример 5: Публичный канал Telegram

```python
# telegram_channel_agent.py
from ..base import BaseAgent, Fetched, ListingEventDraft
import aiohttp
import re

class TelegramChannelAgent(BaseAgent):
    """Агент для мониторинга публичных Telegram каналов"""

    TYPE = "telegram_public"
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "channel_username": {"type": "string"},
            "keywords": {"type": "array", "items": {"type": "string"}},
            "max_posts": {"type": "integer", "default": 50},
            "game_keywords": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["channel_username"]
    }

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
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
        soup = BeautifulSoup(fetched.body, 'html.parser')

        # Ищем посты
        posts = soup.select('.tgme_widget_message')

        keywords = [kw.lower() for kw in self.config.get('keywords', [])]
        game_keywords = [kw.lower() for kw in self.config.get('game_keywords', [])]
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

                # Проверяем упоминания игр
                games_found = self._extract_game_mentions(text, game_keywords)

                # Извлекаем ссылку
                link_elem = post.select_one('a[href*="t.me"]')
                url = link_elem.get('href') if link_elem else fetched.url

                # Определяем тип события
                kind = self._determine_kind_from_text(text)

                yield ListingEventDraft(
                    title=text[:200],  # обрезаем длинные тексты
                    url=url,
                    kind=kind,
                    meta={
                        'source': 'telegram',
                        'channel': self.config['channel_username'],
                        'message_id': post.get('data-post'),
                        'games_found': games_found
                    }
                )

            except Exception as e:
                self.ctx.logger.warning(f"Ошибка обработки поста: {e}")

    def _extract_game_mentions(self, text, game_keywords):
        """Извлекает упоминания игр из текста"""
        found = []
        for keyword in game_keywords:
            if keyword in text:
                found.append(keyword)
        return found

    def _determine_kind_from_text(self, text):
        """Определяет тип события по тексту"""
        if any(word in text for word in ['предзаказ', 'preorder', 'скоро']):
            return 'preorder'
        elif any(word in text for word in ['релиз', 'вышел', 'в продаже']):
            return 'release'
        elif any(word in text for word in ['анонс', 'announce']):
            return 'announce'
        elif any(word in text for word in ['скидка', 'sale', 'discount']):
            return 'discount'

        return 'announce'
```

## 🔧 Утилиты и базовые классы

### Rate Limiter для агентов

```python
# rate_limiter.py
import asyncio
import time
from typing import Dict

class RateLimiter:
    """Класс для управления ограничениями запросов"""

    def __init__(self, config: Dict):
        self.rps = config.get('rps', 1.0)
        self.burst = config.get('burst', 5)
        self.daily_limit = config.get('daily_pages_cap', 1000)

        self.tokens = self.burst
        self.last_refill = time.time()
        self.daily_requests = 0
        self.last_day = time.time() // (24 * 3600)

    async def acquire(self):
        """Получает разрешение на запрос"""
        # Проверка дневного лимита
        current_day = time.time() // (24 * 3600)
        if current_day > self.last_day:
            self.daily_requests = 0
            self.last_day = current_day

        if self.daily_requests >= self.daily_limit:
            raise Exception("Дневной лимит запросов превышен")

        # Проверка RPS
        await self._refill_tokens()

        if self.tokens < 1:
            wait_time = (1 - self.tokens) / self.rps
            await asyncio.sleep(wait_time)
            await self._refill_tokens()

        self.tokens -= 1
        self.daily_requests += 1

    async def _refill_tokens(self):
        """Пополняет токены"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst, self.tokens + elapsed * self.rps)
        self.last_refill = now
```

### Базовый класс для всех агентов

```python
# enhanced_base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, AsyncGenerator
import logging
import asyncio
from datetime import datetime

class EnhancedBaseAgent(ABC):
    """Расширенный базовый класс для всех агентов"""

    def __init__(self, config: Dict[str, Any], secrets: Dict[str, Any], ctx):
        self.config = config
        self.secrets = secrets
        self.ctx = ctx
        self.logger = logging.getLogger(f"agent.{self.__class__.__name__}")
        self.stats = {
            'pages_fetched': 0,
            'events_created': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

    async def run(self) -> AsyncGenerator[ListingEventDraft, None]:
        """Основной метод запуска агента"""
        self.logger.info(f"Запуск агента {self.__class__.__name__}")

        try:
            async for fetched in self.fetch():
                self.stats['pages_fetched'] += 1

                try:
                    async for event in self.parse(fetched):
                        self.stats['events_created'] += 1
                        yield event

                except Exception as e:
                    self.stats['errors'] += 1
                    self.logger.error(f"Ошибка парсинга {fetched.url}: {e}")

        except Exception as e:
            self.logger.error(f"Критическая ошибка агента: {e}")
            raise
        finally:
            self._log_stats()

    @abstractmethod
    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получение данных"""
        pass

    @abstractmethod
    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """Парсинг данных"""
        pass

    def _log_stats(self):
        """Логирует статистику работы"""
        duration = datetime.now() - self.stats['start_time']
        self.logger.info(
            f"Статистика агента: "
            f"страниц: {self.stats['pages_fetched']}, "
            f"событий: {self.stats['events_created']}, "
            f"ошибок: {self.stats['errors']}, "
            f"время: {duration}"
        )
```

## 📋 Советы по созданию агентов

### 1. Планирование

Перед созданием агента:
1. **Изучите структуру** источника данных
2. **Определите тип** агента (HTML, API, Telegram)
3. **Найдите селекторы** или эндпоинты
4. **Определите ограничения** (rate limiting, пагинация)
5. **Продумайте обработку ошибок**

### 2. Разработка

При разработке:
1. **Начните с простого** - базовый парсинг
2. **Добавляйте сложность** постепенно
3. **Тестируйте на реальных данных**
4. **Логируйте важные события**
5. **Обрабатывайте исключения**

### 3. Тестирование

Для тестирования агентов:
1. **Сохраните HTML примеры** в тестовые файлы
2. **Используйте моки** для внешних запросов
3. **Проверяйте граничные случаи**
4. **Тестируйте производительность**
5. **Валидируйте результаты**

### 4. Развертывание

При развертывании:
1. **Создайте манифест** с правильной конфигурацией
2. **Установите консервативные лимиты**
3. **Мониторьте работу** агента
4. **Настройте уведомления** об ошибках
5. **Регулярно обновляйте** при изменениях источника

---

**Используйте эти примеры как основу для создания собственных агентов!** 🚀

Начните с простого агента и постепенно добавляйте функциональность по мере необходимости.