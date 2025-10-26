"""Unit тесты для системы агентов"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import asyncio
import hashlib

from app.agents.base import Fetched, ListingEventDraft, RuntimeContext, BaseAgent


class TestFetched:
    """Тесты для класса Fetched"""

    def test_fetched_creation(self):
        """Тест создания объекта Fetched"""
        url = "https://example.com/page"
        status = 200
        body = "<html>Test content</html>"
        headers = {"Content-Type": "text/html"}
        fetched_at = datetime.utcnow()

        fetched = Fetched(url, status, body, headers, fetched_at)

        assert fetched.url == url
        assert fetched.status == status
        assert fetched.body == body
        assert fetched.headers == headers
        assert fetched.fetched_at == fetched_at

    def test_fetched_hash_property(self):
        """Тест вычисления хэша контента"""
        url = "https://example.com/page"
        body = "<html>Test content</html>"
        headers = {"Content-Type": "text/html"}
        fetched_at = datetime.utcnow()

        fetched = Fetched(url, 200, body, headers, fetched_at)

        # Проверяем, что хэш вычисляется правильно
        expected_content = f"{url}|{body}"
        expected_hash = hashlib.sha256(expected_content.encode()).hexdigest()
        assert fetched.hash == expected_hash

    def test_fetched_hash_uniqueness(self):
        """Тест уникальности хэша для разного контента"""
        fetched1 = Fetched("https://example.com/1", 200, "content1", {}, datetime.utcnow())
        fetched2 = Fetched("https://example.com/2", 200, "content2", {}, datetime.utcnow())
        fetched3 = Fetched("https://example.com/1", 200, "content1", {}, datetime.utcnow())

        assert fetched1.hash != fetched2.hash
        assert fetched1.hash == fetched3.hash  # Одинаковый контент -> одинаковый хэш

    def test_fetched_hash_different_urls(self):
        """Тест хэша для одинакового контента с разных URL"""
        body = "Same content"
        fetched1 = Fetched("https://example.com/page1", 200, body, {}, datetime.utcnow())
        fetched2 = Fetched("https://example.com/page2", 200, body, {}, datetime.utcnow())

        assert fetched1.hash != fetched2.hash


class TestListingEventDraft:
    """Тесты для класса ListingEventDraft"""

    def test_minimal_event_draft(self):
        """Тест создания минимального события"""
        draft = ListingEventDraft(title="Тестовая игра")

        assert draft.title == "Тестовая игра"
        assert draft.url is None
        assert draft.store_id is None
        assert draft.kind is None
        assert draft.price is None
        assert draft.discount_pct is None
        assert draft.edition is None
        assert draft.in_stock is None

    def test_full_event_draft(self):
        """Тест создания полного события"""
        draft = ListingEventDraft(
            title="Громкое дело",
            url="https://example.com/game",
            store_id="test_store",
            kind="release",
            price=1999.99,
            discount_pct=10.0,
            edition="Коллекционное",
            in_stock=True
        )

        assert draft.title == "Громкое дело"
        assert draft.url == "https://example.com/game"
        assert draft.store_id == "test_store"
        assert draft.kind == "release"
        assert draft.price == 1999.99
        assert draft.discount_pct == 10.0
        assert draft.edition == "Коллекционное"
        assert draft.in_stock is True

    def test_price_validation(self):
        """Тест валидации цен"""
        # Корректные значения
        valid_prices = [0.0, 99.99, 1999.90, 5000.0]
        for price in valid_prices:
            draft = ListingEventDraft(title="Игра", price=price)
            assert draft.price == price

        # Отрицательные цены (некорректные, но класс не должен их отбрасывать)
        negative_prices = [-10.0, -0.01]
        for price in negative_prices:
            draft = ListingEventDraft(title="Игра", price=price)
            assert draft.price == price

    def test_discount_validation(self):
        """Тест валидации скидок"""
        # Корректные значения
        valid_discounts = [0.0, 10.0, 25.5, 50.0, 100.0]
        for discount in valid_discounts:
            draft = ListingEventDraft(title="Игра", discount_pct=discount)
            assert draft.discount_pct == discount

        # Скидки больше 100% (некорректные, но возможные)
        high_discounts = [110.0, 150.0]
        for discount in high_discounts:
            draft = ListingEventDraft(title="Игра", discount_pct=discount)
            assert draft.discount_pct == discount


class TestRuntimeContext:
    """Тесты для класса RuntimeContext"""

    @pytest.fixture
    def mock_config(self):
        """Mock конфигурации"""
        return {
            "rate_limit": {"requests_per_minute": 10},
            "schedule": {"interval": "1h"}
        }

    @pytest.fixture
    def mock_secrets(self):
        """Mock секретов"""
        return {"api_key": "test_key"}

    def test_runtime_context_creation(self, mock_config, mock_secrets):
        """Тест создания контекста выполнения"""
        agent_id = "test_agent"
        ctx = RuntimeContext(agent_id, mock_config, mock_secrets)

        assert ctx.agent_id == agent_id
        assert ctx.config == mock_config
        assert ctx.secrets == mock_secrets
        assert ctx.session is None

    @pytest.mark.asyncio
    async def test_runtime_context_async_enter(self, mock_config, mock_secrets):
        """Тест входа в async context"""
        ctx = RuntimeContext("test_agent", mock_config, mock_secrets)

        async with ctx as context:
            assert context is ctx
            assert ctx.session is not None
            assert ctx.session.closed is False

        # После выхода из контекста сессия должна быть закрыта
        assert ctx.session.closed is True

    @pytest.mark.asyncio
    async def test_runtime_context_session_configuration(self, mock_config, mock_secrets):
        """Тест конфигурации сессии"""
        ctx = RuntimeContext("test_agent", mock_config, mock_secrets)

        async with ctx:
            session = ctx.session
            # Проверяем timeout
            assert session._timeout.total == 30
            # Проверяем User-Agent
            assert "BoardGamesMonitor/1.0" in session.headers["User-Agent"]

    @pytest.mark.asyncio
    async def test_runtime_context_exception_handling(self, mock_config, mock_secrets):
        """Тест обработки исключений в контексте"""
        ctx = RuntimeContext("test_agent", mock_config, mock_secrets)

        try:
            async with ctx:
                raise ValueError("Test exception")
        except ValueError:
            pass  # Ожидаемое исключение

        # Сессия должна быть закрыта даже при исключении
        assert ctx.session.closed


class TestBaseAgent:
    """Тесты для базового класса агента"""

    @pytest.fixture
    def mock_config(self):
        """Mock конфигурации агента"""
        return {
            "rate_limit": {"requests_per_minute": 30},
            "schedule": {"interval": "2h"},
            "custom_setting": "value"
        }

    @pytest.fixture
    def mock_secrets(self):
        """Mock секретов агента"""
        return {"secret_token": "test_token"}

    @pytest.fixture
    def mock_ctx(self, mock_config, mock_secrets):
        """Mock контекста выполнения"""
        return RuntimeContext("test_agent", mock_config, mock_secrets)

    def test_base_agent_creation(self, mock_config, mock_secrets, mock_ctx):
        """Тест создания базового агента"""
        class TestAgent(BaseAgent):
            async def fetch(self):
                return
                yield

            async def parse(self, fetched):
                return
                yield

        agent = TestAgent(mock_config, mock_secrets, mock_ctx)

        assert agent.config == mock_config
        assert agent.secrets == mock_secrets
        assert agent.ctx == mock_ctx
        assert agent.rate_limit == {"requests_per_minute": 30}
        assert agent.schedule == {"interval": "2h"}

    def test_base_agent_default_values(self, mock_secrets, mock_ctx):
        """Тест значений по умолчанию"""
        config = {}  # Пустая конфигурация

        class TestAgent(BaseAgent):
            async def fetch(self):
                return
                yield

            async def parse(self, fetched):
                return
                yield

        agent = TestAgent(config, mock_secrets, mock_ctx)

        assert agent.rate_limit == {}
        assert agent.schedule == {}

    def test_base_agent_constants(self):
        """Тест констант базового агента"""
        assert BaseAgent.TYPE == "html"
        assert BaseAgent.CONFIG_SCHEMA == {}

    def test_base_agent_abstract_methods(self, mock_config, mock_secrets, mock_ctx):
        """Тест того, что абстрактные методы требуют реализации"""
        class ConcreteAgent(BaseAgent):
            pass

        # Абстрактные методы должны вызывать TypeError при попытке инстанциирования
        with pytest.raises(TypeError, match="abstract methods"):
            ConcreteAgent(mock_config, mock_secrets, mock_ctx)

    def test_base_agent_with_minimal_implementation(self, mock_config, mock_secrets, mock_ctx):
        """Тест агента с минимальной реализацией"""
        class MinimalAgent(BaseAgent):
            async def fetch(self):
                return
                yield

            async def parse(self, fetched):
                return
                yield

        agent = MinimalAgent(mock_config, mock_secrets, mock_ctx)
        assert agent.TYPE == "html"

    @pytest.mark.asyncio
    async def test_base_agent_run_method(self, mock_config, mock_secrets, mock_ctx):
        """Тест метода run агента"""
        fetched_data = Fetched(
            "https://example.com",
            200,
            "<html>Test</html>",
            {},
            datetime.utcnow()
        )
        event_draft = ListingEventDraft(
            title="Тестовая игра",
            price=999.99,
            store_id="test_store"
        )

        class TestAgent(BaseAgent):
            async def fetch(self):
                yield fetched_data

            async def parse(self, fetched):
                yield event_draft

        agent = TestAgent(mock_config, mock_secrets, mock_ctx)
        results = await agent.run()

        assert len(results) == 1
        assert results[0].title == "Тестовая игра"
        assert results[0].price == 999.99

    @pytest.mark.asyncio
    async def test_base_agent_run_with_multiple_items(self, mock_config, mock_secrets, mock_ctx):
        """Тест метода run с несколькими элементами"""
        fetched_data = [
            Fetched("https://example.com/1", 200, "<html>Test1</html>", {}, datetime.utcnow()),
            Fetched("https://example.com/2", 200, "<html>Test2</html>", {}, datetime.utcnow())
        ]
        event_drafts = [
            ListingEventDraft(title="Игра 1", store_id="test_store"),
            ListingEventDraft(title="Игра 2", store_id="test_store")
        ]

        class TestAgent(BaseAgent):
            async def fetch(self):
                for fetched in fetched_data:
                    yield fetched

            async def parse(self, fetched):
                # Возвращаем разные события для разного контента
                if "Test1" in fetched.body:
                    yield event_drafts[0]
                else:
                    yield event_drafts[1]

        agent = TestAgent(mock_config, mock_secrets, mock_ctx)
        results = await agent.run()

        assert len(results) == 2
        assert results[0].title == "Игра 1"
        assert results[1].title == "Игра 2"

    @pytest.mark.asyncio
    async def test_base_agent_error_handling_in_fetch(self, mock_config, mock_secrets, mock_ctx):
        """Тест обработки ошибок в методе fetch"""
        class TestAgent(BaseAgent):
            async def fetch(self):
                yield Fetched("https://example.com", 200, "content", {}, datetime.utcnow())
                raise Exception("Fetch error after first result")

            async def parse(self, fetched):
                yield ListingEventDraft(title="Test")

        agent = TestAgent(mock_config, mock_secrets, mock_ctx)

        with pytest.raises(Exception, match="Fetch error after first result"):
            await agent.run()

    @pytest.mark.asyncio
    async def test_base_agent_empty_results(self, mock_config, mock_secrets, mock_ctx):
        """Тест агента, который не находит данных"""
        class TestAgent(BaseAgent):
            async def fetch(self):
                yield Fetched("https://example.com", 200, "<html>No data</html>", {}, datetime.utcnow())

            async def parse(self, fetched):
                # Ничего не находим
                return

        agent = TestAgent(mock_config, mock_secrets, mock_ctx)
        results = await agent.run()

        assert len(results) == 0


class TestAgentIntegration:
    """Интеграционные тесты для системы агентов"""

    @pytest.mark.asyncio
    async def test_full_agent_workflow(self):
        """Тест полного рабочего процесса агента"""
        # Создаем тестовые данные
        html_content = """
        <html>
            <body>
                <div class="game">
                    <h2>Тестовая игра</h2>
                    <div class="price">999 ₽</div>
                    <div class="store">Test Store</div>
                </div>
            </body>
        </html>
        """

        fetched = Fetched(
            "https://test-store.com/games",
            200,
            html_content,
            {"Content-Type": "text/html"},
            datetime.utcnow()
        )

        # Создаем простой агент
        class SimpleHTMLAgent(BaseAgent):
            async def fetch(self):
                yield fetched

            async def parse(self, fetched):
                # Простое извлечение данных из HTML
                if "Тестовая игра" in fetched.body:
                    yield ListingEventDraft(
                        title="Тестовая игра",
                        price=999.0,
                        store_id="test_store",
                        url=fetched.url
                    )

        # Настраиваем и запускаем
        config = {"rate_limit": {"requests_per_minute": 10}}
        secrets = {}
        ctx = RuntimeContext("simple_agent", config, secrets)

        agent = SimpleHTMLAgent(config, secrets, ctx)
        results = await agent.run()

        # Проверяем результаты
        assert len(results) == 1
        game = results[0]
        assert game.title == "Тестовая игра"
        assert game.price == 999.0
        assert game.store_id == "test_store"
        assert game.url == "https://test-store.com/games"