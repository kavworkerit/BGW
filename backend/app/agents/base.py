from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime
import asyncio
import aiohttp
import hashlib
import logging

logger = logging.getLogger(__name__)


@dataclass
class Fetched:
    """Данные полученные от источника."""
    url: str
    status: int
    body: str
    headers: Dict[str, str]
    fetched_at: datetime

    @property
    def hash(self) -> str:
        """Хэш контента для дедупликации."""
        content = f"{self.url}|{self.body}"
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class ListingEventDraft:
    """Черновик события о листинге."""
    title: str
    url: Optional[str] = None
    store_id: Optional[str] = None
    kind: Optional[str] = None
    price: Optional[float] = None
    discount_pct: Optional[float] = None
    edition: Optional[str] = None
    in_stock: Optional[bool] = None


class RuntimeContext:
    """Контекст выполнения агента."""

    def __init__(self, agent_id: str, config: Dict[str, Any], secrets: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.secrets = secrets
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'BoardGamesMonitor/1.0'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()


class BaseAgent(ABC):
    """Базовый класс для всех агентов."""

    TYPE = "html"  # 'api' | 'html' | 'headless' | 'telegram_public'
    CONFIG_SCHEMA: Dict[str, Any] = {}

    def __init__(self, config: Dict[str, Any], secrets: Dict[str, Any], ctx: RuntimeContext):
        self.config = config
        self.secrets = secrets
        self.ctx = ctx
        self.rate_limit = config.get('rate_limit', {})
        self.schedule = config.get('schedule', {})

    @abstractmethod
    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """
        Получить данные из источника.

        Yield:
            Fetched: Полученные данные
        """
        pass

    @abstractmethod
    async def parse(self, fetched: Fetched) -> AsyncGenerator[ListingEventDraft, None]:
        """
        Извлечь события из полученных данных.

        Args:
            fetched: Полученные данные

        Yield:
            ListingEventDraft: Извлеченные события
        """
        pass

    async def run(self) -> List[ListingEventDraft]:
        """Запустить агента и вернуть все найденные события."""
        events = []

        async with self.ctx:
            async for fetched in self.fetch():
                try:
                    async for event in self.parse(fetched):
                        events.append(event)
                except Exception as e:
                    logger.error(f"Error parsing {fetched.url}: {e}")
                    continue

        return events

    def validate_config(self) -> bool:
        """Проверить конфигурацию агента."""
        # TODO: Implement JSON Schema validation
        return True


class HTMLAgent(BaseAgent):
    """Агент для работы с HTML страницами."""

    TYPE = "html"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.selectors = self.config.get('selectors', {})
        self.start_urls = self.config.get('start_urls', [])

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получить HTML страницы."""
        for url in self.start_urls:
            try:
                async with self.ctx.session.get(url) as response:
                    if response.status == 200:
                        body = await response.text()
                        yield Fetched(
                            url=url,
                            status=response.status,
                            body=body,
                            headers=dict(response.headers),
                            fetched_at=datetime.now()
                        )
                    else:
                        logger.warning(f"Failed to fetch {url}: {response.status}")

                # Учитываем rate limiting
                if 'rps' in self.rate_limit:
                    await asyncio.sleep(1.0 / self.rate_limit['rps'])

            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                continue


class Agent(BaseAgent):
    """Агент для работы с API."""

    TYPE = "api"

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получить данные из API."""
        # TODO: Implement API fetching logic
        pass


class HeadlessAgent(BaseAgent):
    """Агент для работы с динамическими сайтами через Playwright."""

    TYPE = "headless"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = self.config.get('start_urls', [])
        self.selectors = self.config.get('selectors', {})
        self.wait_for = self.config.get('wait_for', None)
        self.screenshot = self.config.get('screenshot', False)

    async def fetch(self) -> AsyncGenerator[Fetched, None]:
        """Получить HTML через Playwright."""
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='BoardGamesMonitor/1.0',
                viewport={'width': 1920, 'height': 1080}
            )

            for url in self.start_urls:
                try:
                    page = await context.new_page()
                    await page.goto(url, wait_until='networkidle')

                    # Ждем появления элементов если нужно
                    if self.wait_for:
                        await page.wait_for_selector(self.wait_for, timeout=10000)

                    # Делаем скриншот если нужно
                    if self.screenshot:
                        screenshot_path = f"screenshot_{int(datetime.now().timestamp())}.png"
                        await page.screenshot(path=screenshot_path)
                        logger.info(f"Screenshot saved: {screenshot_path}")

                    # Получаем HTML
                    body = await page.content()

                    yield Fetched(
                        url=url,
                        status=200,
                        body=body,
                        headers={},  # Playwright headers are complex
                        fetched_at=datetime.now()
                    )

                    await page.close()

                    # Учитываем rate limiting
                    if 'rps' in self.rate_limit:
                        await asyncio.sleep(1.0 / self.rate_limit['rps'])

                except Exception as e:
                    logger.error(f"Error fetching {url} with Playwright: {e}")
                    continue

            await browser.close()