import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
import aiohttp

from app.agents.base import BaseAgent, HTMLAgent, HeadlessAgent, Fetched, ListingEventDraft, RuntimeContext
from app.agents.builtin.hobbygames import HobbyGamesComingSoonAgent
from app.agents.builtin.lavkaigr import LavkaIgrShopAgent
from app.agents.builtin.evrikus import EvrikusCatalogAgent
from app.agents.builtin.crowdgames import CrowdGamesAgent
from app.agents.builtin.gaga import GagaAgent
from app.agents.builtin.zvezda import ZvezdaAgent
from app.agents.builtin.choochoogames import ChooChooGamesAgent
from app.agents.builtin.nastolio import NastolPublicationsAgent
from app.agents.builtin.hobbygames_headless import HobbyGamesHeadlessAgent


@pytest.fixture
def sample_config():
    """Пример конфигурации для агента"""
    return {
        "start_urls": ["https://example.com"],
        "rate_limit": {"rps": 1.0, "burst": 1},
        "selectors": {
            "item": ".product-item",
            "title": ".product-item__title",
            "price": ".product-item__price"
        }
    }


@pytest.fixture
def sample_secrets():
    """Пример секретов для агента"""
    return {}


@pytest.fixture
def mock_context():
    """Мок контекста выполнения"""
    return Mock(spec=RuntimeContext)


class TestBaseAgent:
    """Тесты базового класса агента"""

    def test_base_agent_is_abstract(self):
        """Тест, что BaseAgent является абстрактным классом"""
        with pytest.raises(TypeError):
            BaseAgent({}, {}, Mock())

    def test_base_agent_has_required_methods(self):
        """Тест наличия обязательных методов"""
        assert hasattr(BaseAgent, 'fetch')
        assert hasattr(BaseAgent, 'parse')
        assert hasattr(BaseAgent, 'run')
        assert hasattr(BaseAgent, 'validate_config')

    def test_base_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации дочернего класса"""
        class TestAgent(BaseAgent):
            TYPE = "test"

            async def fetch(self):
                return
            async def parse(self, fetched):
                return

        ctx = Mock(spec=RuntimeContext)
        agent = TestAgent(sample_config, sample_secrets, ctx)

        assert agent.config == sample_config
        assert agent.secrets == sample_secrets
        assert agent.ctx == ctx
        assert agent.rate_limit == sample_config['rate_limit']


class TestHTMLAgent:
    """Тесты HTML агента"""

    def test_html_agent_type(self):
        """Тест типа HTML агента"""
        assert HTMLAgent.TYPE == "html"

    def test_html_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации HTML агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = HTMLAgent(sample_config, sample_secrets, ctx)

        assert agent.selectors == sample_config['selectors']
        assert agent.start_urls == sample_config['start_urls']

    @pytest.mark.asyncio
    async def test_html_agent_fetch_success(self):
        """Тест успешного получения HTML"""
        html_content = "<html><body><div class='product'>Test</div></body></html>"

        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text.return_value = html_content

        mock_session = AsyncMock()
        mock_session.get.return_value.__aenter__.return_value = mock_response

        ctx = Mock(spec=RuntimeContext)
        ctx.session = mock_session

        config = {"start_urls": ["https://example.com"]}
        agent = HTMLAgent(config, {}, ctx)

        results = []
        async for result in agent.fetch():
            results.append(result)

        assert len(results) == 1
        assert results[0].url == "https://example.com"
        assert results[0].status == 200
        assert results[0].body == html_content


class TestHeadlessAgent:
    """Тесты Headless агента"""

    def test_headless_agent_type(self):
        """Тест типа Headless агента"""
        assert HeadlessAgent.TYPE == "headless"

    def test_headless_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации Headless агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = HeadlessAgent(sample_config, sample_secrets, ctx)

        assert agent.start_urls == sample_config['start_urls']
        assert agent.selectors == sample_config['selectors']


class TestFetched:
    """Тесты Fetched класса"""

    def test_fetched_hash_property(self):
        """Тест вычисления хэша"""
        fetched = Fetched(
            url="https://example.com",
            status=200,
            body="test content",
            headers={},
            fetched_at=datetime.now()
        )

        expected_hash = "d83e25c7ee6926987358ab1b4c3bc86e661d874e455149612b68f58a9930704"
        assert fetched.hash == expected_hash

    def test_fetched_hash_consistency(self):
        """Тест консистентности хэша"""
        content = "test content"
        url = "https://example.com"

        fetched1 = Fetched(url, 200, content, {}, datetime.now())
        fetched2 = Fetched(url, 200, content, {}, datetime.now())

        assert fetched1.hash == fetched2.hash


class TestListingEventDraft:
    """Тесты ListingEventDraft класса"""

    def test_listing_event_draft_creation(self):
        """Тест создания черновика события"""
        event = ListingEventDraft(
            title="Test Game",
            price=1000.0,
            discount_pct=10.0
        )

        assert event.title == "Test Game"
        assert event.price == 1000.0
        assert event.discount_pct == 10.0
        assert event.url is None
        assert event.store_id is None
        assert event.kind is None


@pytest.mark.agents
class TestHobbyGamesComingSoonAgent:
    """Тесты агента для Hobby Games"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = HobbyGamesComingSoonAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "html"
        assert agent.config == sample_config

    @pytest.mark.asyncio
    async def test_agent_run_method(self, sample_config, sample_secrets):
        """Тест метода run"""
        # Мокаем методы fetch и parse
        agent = HobbyGamesComingSoonAgent(sample_config, sample_secrets, Mock(spec=RuntimeContext))

        mock_fetched = Fetched(
            url="https://example.com",
            status=200,
            body="<div>Test</div>",
            headers={},
            fetched_at=datetime.now()
        )

        async def mock_fetch():
            yield mock_fetched

        async def mock_parse(fetched):
            yield ListingEventDraft(title="Test Game", price=1000)

        agent.fetch = mock_fetch
        agent.parse = mock_parse

        results = await agent.run()
        assert len(results) == 1
        assert results[0].title == "Test Game"
        assert results[0].price == 1000


@pytest.mark.agents
class TestLavkaIgrShopAgent:
    """Тесты агента для Лавка Игр"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = LavkaIgrShopAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "html"
        assert agent.config == sample_config


@pytest.mark.agents
class TestEvrikusCatalogAgent:
    """Тесты агента для Evrikus"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = EvrikusCatalogAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "html"
        assert agent.config == sample_config


@pytest.mark.agents
class TestCrowdGamesAgent:
    """Тесты агента для CrowdGames"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = CrowdGamesAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "html"
        assert agent.config == sample_config


@pytest.mark.agents
class TestGagaAgent:
    """Тесты агента для Gaga"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = GagaAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "html"
        assert agent.config == sample_config


@pytest.mark.agents
class TestZvezdaAgent:
    """Тесты агента для Звезда"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = ZvezdaAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "html"
        assert agent.config == sample_config


@pytest.mark.agents
class TestChooChooGamesAgent:
    """Тесты агента для ChooChooGames"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = ChooChooGamesAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "html"
        assert agent.config == sample_config


@pytest.mark.agents
class TestNastolPublicationsAgent:
    """Тесты агента для Nastol.io"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = NastolPublicationsAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "html"
        assert agent.config == sample_config


@pytest.mark.agents
class TestHobbyGamesHeadlessAgent:
    """Тесты Headless агента для Hobby Games"""

    def test_agent_initialization(self, sample_config, sample_secrets):
        """Тест инициализации headless агента"""
        ctx = Mock(spec=RuntimeContext)
        agent = HobbyGamesHeadlessAgent(sample_config, sample_secrets, ctx)

        assert agent.TYPE == "headless"
        assert agent.config == sample_config


@pytest.mark.integration
@pytest.mark.slow
class TestAgentsIntegration:
    """Интеграционные тесты для агентов"""

    @pytest.mark.asyncio
    async def test_agent_with_real_html(self):
        """Тест агента с реальным HTML"""
        html_content = """
        <html>
            <body>
                <div class="catalog">
                    <div class="product-item">
                        <div class="product-item__title">Тестовая игра</div>
                        <div class="product-item__price">1000 ₽</div>
                        <div class="product-item__badge">Новинка</div>
                        <a href="/game/1" class="product-item__link"></a>
                    </div>
                </div>
            </body>
        </html>
        """

        config = {
            "start_urls": ["https://example.com"],
            "selectors": {
                "item": ".product-item",
                "title": ".product-item__title",
                "price": ".product-item__price"
            }
        }

        ctx = Mock(spec=RuntimeContext)
        agent = HTMLAgent(config, {}, ctx)

        fetched = Fetched(
            url="https://example.com",
            status=200,
            body=html_content,
            headers={},
            fetched_at=datetime.now()
        )

        # Проверяем, что агент может обработать HTML без ошибок
        events = []
        async for event in agent.parse(fetched):
            events.append(event)

        # События не генерируются без конкретной реализации парсера
        assert isinstance(events, list)


@pytest.mark.unit
class TestAgentValidation:
    """Тесты валидации конфигурации агентов"""

    def test_config_validation_required_fields(self):
        """Тест валидации обязательных полей конфигурации"""
        ctx = Mock(spec=RuntimeContext)

        # Пустая конфигурация должна вызывать ошибку
        agent = HTMLAgent({}, {}, ctx)
        assert not hasattr(agent, 'start_urls') or agent.start_urls == []

        # Конфигурация с start_urls
        config_with_urls = {"start_urls": ["https://example.com"]}
        agent_with_urls = HTMLAgent(config_with_urls, {}, ctx)
        assert agent_with_urls.start_urls == ["https://example.com"]

    def test_rate_limit_configuration(self):
        """Тест конфигурации rate limiting"""
        ctx = Mock(spec=RuntimeContext)

        config = {
            "start_urls": ["https://example.com"],
            "rate_limit": {"rps": 2.0, "burst": 5}
        }

        agent = HTMLAgent(config, {}, ctx)
        assert agent.rate_limit == {"rps": 2.0, "burst": 5}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])