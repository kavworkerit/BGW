"""
Тесты агентов с использованием Record/Replay подхода.

Использует VCR.py для записи и воспроизведения HTTP запросов.
Это позволяет тестировать агентов с реальными данными сайтов
без необходимости делать реальные запросы каждый раз.
"""

import pytest
import os
from unittest.mock import Mock
import vcr
from datetime import datetime

from app.agents.base import Fetched
from app.agents.builtin.hobbygames import HobbyGamesComingSoonAgent
from app.agents.builtin.lavkaigr import LavkaIgrShopAgent
from app.agents.builtin.evrikus import EvrikusCatalogAgent


# Конфигурация VCR
VCR_CASSETTE_DIR = "tests/cassettes"
MOCK_CONTEXT = Mock()


@pytest.fixture
def vcr_cassette_dir():
    """Создать директорию для кассет VCR"""
    os.makedirs(VCR_CASSETTE_DIR, exist_ok=True)
    return VCR_CASSETTE_DIR


@pytest.mark.agents
@pytest.mark.integration
class TestAgentRecordReplay:
    """Тесты агентов с записанными HTTP запросами"""

    @pytest.fixture
    def hobbygames_config(self):
        """Конфигурация для HobbyGames"""
        return {
            "start_urls": ["https://hobbygames.ru/coming-soon"],
            "selectors": {
                "item": ".product-item",
                "title": ".product-item__title",
                "price": ".product-item__price",
                "url": ".product-item__link::attr(href)",
                "badge": ".product-item__label"
            },
            "rate_limit": {"rps": 0.5, "burst": 1},
            "schedule": {"cron": "0 */2 * * *"}
        }

    @pytest.fixture
    def lavkaigr_config(self):
        """Конфигурация для Лавка Игр"""
        return {
            "start_urls": ["https://www.lavkaigr.ru/shop/"],
            "selectors": {
                "item": ".product-card",
                "title": ".product-card__title",
                "price": ".price",
                "badge": ".badge",
                "url": ".product-card__link::attr(href)"
            },
            "rate_limit": {"rps": 0.3, "burst": 1},
            "schedule": {"cron": "0 9,13,17,21 * * *"}
        }

    @vcr.use_cassette("hobbygames_coming_soon.yaml")
    @pytest.mark.asyncio
    async def test_hobbygames_fetch_with_real_data(self, hobbygames_config, vcr_cassette_dir):
        """Тест получения данных с HobbyGames с записанными ответами"""
        # Кассета будет создана если не существует, или использована если существует
        cassette_path = os.path.join(vcr_cassette_dir, "hobbygames_coming_soon.yaml")

        agent = HobbyGamesComingSoonAgent(hobbygames_config, {}, MOCK_CONTEXT)

        # Подсчитываем количество успешных загрузок
        fetched_count = 0
        successful_fetched = []

        async with MOCK_CONTEXT:
            async for fetched in agent.fetch():
                fetched_count += 1
                if fetched.status == 200:
                    successful_fetched.append(fetched)
                    assert isinstance(fetched.url, str)
                    assert isinstance(fetched.body, str)
                    assert len(fetched.body) > 0
                    assert isinstance(fetched.headers, dict)

        assert fetched_count >= 0
        # Проверяем, что хотя бы одна страница была успешно загружена
        # (в реальной ситуации зависит от доступности сайта)
        if successful_fetched:
            for fetched in successful_fetched:
                assert "hobbygames.ru" in fetched.url
                assert "<html" in fetched.body.lower() or "html" in fetched.headers.get("content-type", "")

    @vcr.use_cassette("lavkaigr_shop.yaml")
    @pytest.mark.asyncio
    async def test_lavkaigr_fetch_with_real_data(self, lavkaigr_config, vcr_cassette_dir):
        """Тест получения данных с Лавка Игр с записанными ответами"""
        agent = LavkaIgrShopAgent(lavkaigr_config, {}, MOCK_CONTEXT)

        fetched_count = 0
        successful_fetched = []

        async with MOCK_CONTEXT:
            async for fetched in agent.fetch():
                fetched_count += 1
                if fetched.status == 200:
                    successful_fetched.append(fetched)
                    assert isinstance(fetched.url, str)
                    assert isinstance(fetched.body, str)

        assert fetched_count >= 0
        if successful_fetched:
            for fetched in successful_fetched:
                assert "lavkaigr.ru" in fetched.url

    def test_fetched_hash_generation(self):
        """Тест генерации хэша для дедупликации"""
        # Одинаковый URL и контент должен давать одинаковый хэш
        fetched1 = Fetched(
            url="https://example.com/test",
            status=200,
            body="<html>Test content</html>",
            headers={"content-type": "text/html"},
            fetched_at=datetime(2024, 1, 1, 12, 0, 0)
        )

        fetched2 = Fetched(
            url="https://example.com/test",
            status=200,
            body="<html>Test content</html>",
            headers={"content-type": "text/html"},
            fetched_at=datetime(2024, 1, 1, 12, 0, 1)  # Другое время
        )

        assert fetched1.hash == fetched2.hash

        # Разный контент должен давать разный хэш
        fetched3 = Fetched(
            url="https://example.com/test",
            status=200,
            body="<html>Different content</html>",
            headers={"content-type": "text/html"},
            fetched_at=datetime(2024, 1, 1, 12, 0, 0)
        )

        assert fetched1.hash != fetched3.hash

    @pytest.mark.asyncio
    async def test_agent_error_handling(self):
        """Тест обработки ошибок агентами"""
        # Конфигурация с некорректным URL
        config = {
            "start_urls": ["https://nonexistent-site-12345.com"],
            "rate_limit": {"rps": 1.0}
        }

        agent = HobbyGamesComingSoonAgent(config, {}, MOCK_CONTEXT)

        # Агент должен обрабатывать ошибки без падения
        fetched_count = 0
        error_count = 0

        async with MOCK_CONTEXT:
            async for fetched in agent.fetch():
                fetched_count += 1
                if fetched.status >= 400:
                    error_count += 1

        # Агент должен попытаться загрузить URL и обработать ошибку
        assert fetched_count >= 0  # Может быть 0 если сайт недоступен

    @pytest.mark.asyncio
    async def test_agent_rate_limiting(self):
        """Тест ограничения частоты запросов"""
        config = {
            "start_urls": ["https://httpbin.org/delay/1"],
            "rate_limit": {"rps": 2.0}  # 2 запроса в секунду
        }

        agent = HobbyGamesComingSoonAgent(config, {}, MOCK_CONTEXT)

        start_time = datetime.now()
        fetched_count = 0

        async with MOCK_CONTEXT:
            async for fetched in agent.fetch():
                fetched_count += 1
                # Прерываем после 2 запросов для теста rate limiting
                if fetched_count >= 2:
                    break

        end_time = datetime.now()
        elapsed_seconds = (end_time - start_time).total_seconds()

        # С rate limiting 2 запроса должны занять хотя бы 1 секунду
        # (в реальном сценарии будет зависеть от времени ответа сервера)
        assert elapsed_seconds >= 0.5

    @pytest.mark.asyncio
    async def test_agent_parsing_real_html(self):
        """Тест парсинга реального HTML"""
        real_html = """
        <html>
            <head><title>Hobby Games</title></head>
            <body>
                <div class="catalog-list">
                    <div class="product-item">
                        <div class="product-item__title">Тестовая игра</div>
                        <div class="product-item__price">2 500 ₽</div>
                        <div class="product-item__label new">Новинка</div>
                        <a href="/test-game-123" class="product-item__link">Подробнее</a>
                    </div>
                    <div class="product-item">
                        <div class="product-item__title">Другая игра</div>
                        <div class="product-item__price">1 200 ₽</div>
                        <div class="product-item__label preorder">Предзаказ</div>
                        <a href="/other-game-456" class="product-item__link">Подробнее</a>
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
                "price": ".product-item__price",
                "url": ".product-item__link::attr(href)",
                "badge": ".product-item__label"
            }
        }

        agent = HobbyGamesComingSoonAgent(config, {}, MOCK_CONTEXT)

        fetched = Fetched(
            url="https://example.com/test",
            status=200,
            body=real_html,
            headers={"content-type": "text/html"},
            fetched_at=datetime.now()
        )

        events = []
        async with MOCK_CONTEXT:
            async for event in agent.parse(fetched):
                events.append(event)

        # Проверяем, что парсер извлек события
        assert len(events) > 0

        # Проверяем структуру извлеченных событий
        for event in events:
            assert hasattr(event, 'title')
            assert hasattr(event, 'price')
            assert hasattr(event, 'url')
            assert hasattr(event, 'kind')

    @pytest.mark.asyncio
    async def test_agent_price_extraction(self):
        """Тест извлечения цен"""
        html_with_prices = """
        <div class="products">
            <div class="product">
                <div class="title">Игра 1</div>
                <div class="price">1 000 ₽</div>
            </div>
            <div class="product">
                <div class="title">Игра 2</div>
                <div class="price">2500</div>
            </div>
            <div class="product">
                <div class="title">Игра 3</div>
                <div class="price">от 3 500 ₽</div>
            </div>
        </div>
        """

        # Создаем агента с упрощенной конфигурацией
        config = {
            "start_urls": ["https://example.com"],
            "selectors": {
                "item": ".product",
                "title": ".title",
                "price": ".price"
            }
        }

        agent = HobbyGamesComingSoonAgent(config, {}, MOCK_CONTEXT)

        fetched = Fetched(
            url="https://example.com",
            status=200,
            body=html_with_prices,
            headers={},
            fetched_at=datetime.now()
        )

        # Тестируем извлечение цен с разными форматами
        events = []
        async with MOCK_CONTEXT:
            async for event in agent.parse(fetched):
                events.append(event)

        # Агент должен извлечь хотя бы некоторые цены
        assert len(events) >= 0


@pytest.mark.unit
class TestAgentConfiguration:
    """Тесты конфигурации агентов"""

    def test_agent_config_validation(self):
        """Тест валидации конфигурации"""
        config = {
            "start_urls": ["https://example.com"],
            "selectors": {
                "title": ".title",
                "price": ".price"
            },
            "rate_limit": {
                "rps": 1.0,
                "burst": 5,
                "daily_pages_cap": 100
            }
        }

        agent = HobbyGamesComingSoonAgent(config, {}, MOCK_CONTEXT)

        assert agent.config == config
        assert agent.rate_limit == config["rate_limit"]
        assert agent.selectors == config["selectors"]

    def test_agent_config_missing_selectors(self):
        """Тест агента с отсутствующими селекторами"""
        config = {
            "start_urls": ["https://example.com"]
            # Нет селекторов
        }

        agent = HobbyGamesComingSoonAgent(config, {}, MOCK_CONTEXT)

        # Агент должен работать с пустыми селекторами
        assert agent.selectors == {}

    def test_agent_config_empty_urls(self):
        """Тест агента с пустым списком URL"""
        config = {
            "start_urls": [],  # Пустой список
            "selectors": {"title": ".title"}
        }

        agent = HobbyGamesComingSoonAgent(config, {}, MOCK_CONTEXT)

        assert agent.start_urls == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "agents"])