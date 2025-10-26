"""
Тесты API эндпоинтов приложения.

Проверяют корректность работы REST API, обработку ошибок,
валидацию данных и форматы ответов.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
from datetime import datetime, timedelta
from uuid import uuid4

from app.main import app


@pytest.fixture
def client():
    """Создать тестовый клиент FastAPI"""
    return TestClient(app)


@pytest.fixture
def mock_db():
    """Мок базы данных"""
    return Mock()


@pytest.fixture
def sample_game():
    """Пример данных игры"""
    return {
        "id": str(uuid4()),
        "title": "Тестовая игра",
        "synonyms": ["Test Game", "Игра тестовая"],
        "bgg_id": "123456",
        "publisher": "Тестовый издатель",
        "tags": ["стратегия", "семейная"],
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_agent():
    """Пример данных агента"""
    return {
        "id": "test-agent",
        "name": "Тестовый агент",
        "type": "html",
        "schedule": {"cron": "0 */2 * * *"},
        "rate_limit": {"rps": 1.0, "burst": 1},
        "config": {
            "start_urls": ["https://example.com"],
            "selectors": {"title": ".title"}
        },
        "enabled": True,
        "created_at": datetime.now().isoformat()
    }


@pytest.fixture
def sample_rule():
    """Пример правила уведомлений"""
    return {
        "id": str(uuid4()),
        "name": "Тестовое правило",
        "logic": "AND",
        "conditions": [
            {
                "field": "price",
                "operator": "<=",
                "value": 1000
            },
            {
                "field": "store_id",
                "operator": "in",
                "value": ["hobbygames", "lavkaigr"]
            }
        ],
        "channels": ["webpush"],
        "cooldown_hours": 12,
        "enabled": True,
        "created_at": datetime.now().isoformat()
    }


@pytest.mark.api
class TestHealthEndpoint:
    """Тесты эндпоинта здоровья"""

    def test_healthz_success(self, client):
        """Т successful health check"""
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.api
class TestGamesEndpoint:
    """Тесты эндпоинтов для работы с играми"""

    def test_get_games_empty(self, client, mock_db):
        """Тест получения пустого списка игр"""
        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.all.return_value = []

            response = client.get("/api/games")

            assert response.status_code == 200
            assert response.json() == []

    def test_get_games_with_data(self, client, mock_db, sample_game):
        """Тест получения списка игр с данными"""
        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.all.return_value = [sample_game]

            response = client.get("/api/games")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == sample_game["title"]

    def test_create_game_success(self, client, mock_db):
        """Тест успешного создания игры"""
        game_data = {
            "title": "Новая игра",
            "synonyms": ["New Game"],
            "bgg_id": "789012",
            "publisher": "Издатель X",
            "tags": ["эко"]
        }

        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None

            response = client.post("/api/games", json=game_data)

            assert response.status_code == 201
            data = response.json()
            assert data["title"] == game_data["title"]
            assert "id" in data

    def test_create_game_validation_error(self, client):
        """Тест валидации при создании игры"""
        # Отсутствует обязательное поле title
        invalid_data = {
            "synonyms": ["Invalid Game"],
            "bgg_id": "123"
        }

        response = client.post("/api/games", json=invalid_data)

        assert response.status_code == 422
        assert "detail" in response.json()

    def test_update_game_success(self, client, mock_db, sample_game):
        """Тест успешного обновления игры"""
        update_data = {"title": "Обновленное название"}
        game_id = sample_game["id"]

        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.filter.return_value.first.return_value = sample_game
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = None

            response = client.put(f"/api/games/{game_id}", json=update_data)

            assert response.status_code == 200

    def test_update_game_not_found(self, client, mock_db):
        """Тест обновления несуществующей игры"""
        game_id = str(uuid4())
        update_data = {"title": "Обновленное название"}

        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.filter.return_value.first.return_value = None

            response = client.put(f"/api/games/{game_id}", json=update_data)

            assert response.status_code == 404

    def test_delete_game_success(self, client, mock_db, sample_game):
        """Тест успешного удаления игры"""
        game_id = sample_game["id"]

        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.filter.return_value.first.return_value = sample_game
            mock_db.delete.return_value = None
            mock_db.commit.return_value = None

            response = client.delete(f"/api/games/{game_id}")

            assert response.status_code == 200

    def test_delete_game_not_found(self, client, mock_db):
        """Тест удаления несуществующей игры"""
        game_id = str(uuid4())

        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.filter.return_value.first.return_value = None

            response = client.delete(f"/api/games/{game_id}")

            assert response.status_code == 404


@pytest.mark.api
class TestAgentsEndpoint:
    """Тесты эндпоинтов для работы с агентами"""

    def test_get_agents(self, client, mock_db):
        """Тест получения списка агентов"""
        with patch('app.api.agents.get_db', return_value=mock_db):
            mock_db.query.return_value.all.return_value = []

            response = client.get("/api/agents")

            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_create_agent_success(self, client, mock_db, sample_agent):
        """Тест успешного создания агента"""
        agent_data = {
            "id": "new-agent",
            "name": "Новый агент",
            "type": "html",
            "schedule": {"cron": "0 */4 * * *"},
            "rate_limit": {"rps": 0.5, "burst": 1},
            "config": {
                "start_urls": ["https://example.com"],
                "selectors": {"title": ".title"}
            },
            "enabled": True
        }

        with patch('app.api.agents.get_db', return_value=mock_db):
            response = client.post("/api/agents", json=agent_data)

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == agent_data["name"]

    def test_run_agent_success(self, client, mock_db, sample_agent):
        """Тест запуска агента"""
        agent_id = sample_agent["id"]

        with patch('app.api.agents.get_db', return_value=mock_db):
            with patch('app.services.agent_service.AgentService.run_agent') as mock_run:
                mock_run.return_value = {"status": "started", "events_count": 5}

                response = client.post(f"/api/agents/{agent_id}/run")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "started"


@pytest.mark.api
class TestEventsEndpoint:
    """Тесты эндпоинтов для работы с событиями"""

    def test_get_events_with_filters(self, client, mock_db):
        """Тест получения событий с фильтрацией"""
        params = {
            "game_id": str(uuid4()),
            "store_id": "hobbygames",
            "kind": "discount",
            "limit": 10,
            "offset": 0
        }

        with patch('app.api.events.get_db', return_value=mock_db):
            mock_db.query.return_value.all.return_value = []

            response = client.get("/api/events", params=params)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_get_events_invalid_parameters(self, client):
        """Тест получения событий с невалидными параметрами"""
        params = {
            "limit": "invalid",  # Должен быть числом
            "min_discount": "not_a_number"  # Должен быть числом
        }

        response = client.get("/api/events", params=params)

        assert response.status_code == 422


@pytest.mark.api
class TestRulesEndpoint:
    """Тесты эндпоинтов для работы с правилами"""

    def test_get_rules(self, client, mock_db):
        """Тест получения списка правил"""
        with patch('app.api.rules.get_db', return_value=mock_db):
            mock_db.query.return_value.all.return_value = []

            response = client.get("/api/rules")

            assert response.status_code == 200
            assert isinstance(response.json(), list)

    def test_create_rule_success(self, client, mock_db):
        """Тест успешного создания правила"""
        rule_data = {
            "name": "Новое правило",
            "logic": "OR",
            "conditions": [
                {
                    "field": "discount_pct",
                    "operator": ">=",
                    "value": 20
                }
            ],
            "channels": ["webpush", "telegram"],
            "cooldown_hours": 6,
            "enabled": True
        }

        with patch('app.api.rules.get_db', return_value=mock_db):
            response = client.post("/api/rules", json=rule_data)

            assert response.status_code == 201
            data = response.json()
            assert data["name"] == rule_data["name"]
            assert data["logic"] == rule_data["logic"]

    def test_test_rule_success(self, client, mock_db, sample_rule):
        """Тест тестирования правила"""
        rule_id = sample_rule["id"]

        with patch('app.api.rules.get_db', return_value=mock_db):
            with patch('app.services.notification_service.NotificationService.test_rule') as mock_test:
                mock_test.return_value = {
                    "total_events": 100,
                    "matched_events": 15,
                    "match_rate": 0.15
                }

                response = client.post(f"/api/rules/{rule_id}/test")

                assert response.status_code == 200
                data = response.json()
                assert "total_events" in data
                assert "matched_events" in data
                assert "match_rate" in data


@pytest.mark.api
class TestPricesEndpoint:
    """Тесты эндпоинтов для работы с ценами"""

    def test_get_prices_success(self, client, mock_db):
        """Тест получения истории цен"""
        params = {
            "game_id": str(uuid4()),
            "store_id": "hobbygames",
            "from_date": (datetime.now() - timedelta(days=30)).isoformat(),
            "to_date": datetime.now().isoformat()
        }

        with patch('app.api.prices.get_db', return_value=mock_db):
            mock_db.query.return_value.all.return_value = []

            response = client.get("/api/prices", params=params)

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_export_prices_csv(self, client, mock_db):
        """Тест экспорта цен в CSV"""
        params = {
            "game_id": str(uuid4()),
            "format": "csv"
        }

        with patch('app.api.prices.get_db', return_value=mock_db):
            mock_db.query.return_value.all.return_value = []

            response = client.get("/api/prices/export", params=params)

            assert response.status_code == 200
            assert "text/csv" in response.headers.get("content-type", "")


@pytest.mark.api
class TestNotificationsEndpoint:
    """Тесты эндпоинтов для работы с уведомлениями"""

    def test_get_notifications(self, client, mock_db):
        """Тест получения списка уведомлений"""
        with patch('app.api.notifications.get_db', return_value=mock_db):
            mock_db.query.return_value.all.return_value = []

            response = client.get("/api/notifications")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)

    def test_test_webpush_notification(self, client, mock_db):
        """Тест тестового Web Push уведомления"""
        test_data = {
            "title": "Тестовое уведомление",
            "body": "Это тестовое уведомление",
            "url": "https://example.com"
        }

        with patch('app.api.notifications.get_db', return_value=mock_db):
            with patch('app.services.webpush_service.WebPushService.send_notification') as mock_send:
                mock_send.return_value = {"status": "sent"}

                response = client.post("/api/notifications/test/webpush", json=test_data)

                assert response.status_code == 200


@pytest.mark.api
@pytest.mark.integration
class TestAPIIntegration:
    """Интеграционные тесты API"""

    def test_full_game_lifecycle(self, client, mock_db):
        """Тест полного жизненного цикла игры"""
        # 1. Создание игры
        game_data = {
            "title": "Интеграционная игра",
            "synonyms": ["Integration Game"],
            "tags": ["тест"]
        }

        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.add.return_value = None
            mock_db.commit.return_value = None
            mock_db.refresh.return_value = Mock(id="test-game-id")

            create_response = client.post("/api/games", json=game_data)
            assert create_response.status_code == 201
            created_game = create_response.json()

        # 2. Получение игры
        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.filter.return_value.first.return_value = created_game

            get_response = client.get(f"/api/games/{created_game['id']}")
            assert get_response.status_code == 200
            retrieved_game = get_response.json()
            assert retrieved_game["title"] == game_data["title"]

        # 3. Обновление игры
        update_data = {"title": "Обновленная интеграционная игра"}
        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.filter.return_value.first.return_value = created_game
            mock_db.commit.return_value = None

            update_response = client.put(f"/api/games/{created_game['id']}", json=update_data)
            assert update_response.status_code == 200

        # 4. Удаление игры
        with patch('app.api.games.get_db', return_value=mock_db):
            mock_db.query.return_value.filter.return_value.first.return_value = created_game
            mock_db.delete.return_value = None
            mock_db.commit.return_value = None

            delete_response = client.delete(f"/api/games/{created_game['id']}")
            assert delete_response.status_code == 200


@pytest.mark.api
class TestAPIErrorHandling:
    """Тесты обработки ошибок API"""

    def test_404_not_found(self, client):
        """Тест обработки 404 ошибки"""
        response = client.get("/api/nonexistent-endpoint")
        assert response.status_code == 404

    def test_invalid_json(self, client):
        """Тест обработки невалидного JSON"""
        response = client.post(
            "/api/games",
            data="invalid json",
            headers={"content-type": "application/json"}
        )
        assert response.status_code == 422

    def test_method_not_allowed(self, client):
        """Тест неподдерживаемого HTTP метода"""
        response = client.patch("/api/games")  # PATCH не поддерживается
        assert response.status_code == 405

    def test_large_payload(self, client):
        """Тест обработки слишком большого payload"""
        large_data = {"title": "x" * 10000}  # Очень длинное название

        response = client.post("/api/games", json=large_data)
        # Должен вернуть ошибку валидации
        assert response.status_code >= 400


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "api"])