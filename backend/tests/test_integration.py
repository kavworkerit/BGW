import pytest
from unittest.mock import patch


@pytest.mark.integration
class TestIntegration:
    """Интеграционные тесты"""

    def test_full_game_workflow(self, client, sample_game):
        """Тест полного цикла работы с игрой"""
        # 1. Создание игры
        create_response = client.post("/api/games", json=sample_game)
        assert create_response.status_code == 201
        game_id = create_response.json()["id"]

        # 2. Получение игры
        get_response = client.get(f"/api/games/{game_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == sample_game["title"]

        # 3. Обновление игры
        update_data = {"synonyms": ["Новый синоним"]}
        update_response = client.put(f"/api/games/{game_id}", json=update_data)
        assert update_response.status_code == 200
        assert "Новый синоним" in update_response.json()["synonyms"]

        # 4. Удаление игры
        delete_response = client.delete(f"/api/games/{game_id}")
        assert delete_response.status_code == 200

        # 5. Проверка отсутствия игры
        final_get = client.get(f"/api/games/{game_id}")
        assert final_get.status_code == 404

    def test_full_store_workflow(self, client, sample_store):
        """Тест полного цикла работы с магазином"""
        # 1. Создание магазина
        create_response = client.post("/api/stores", json=sample_store)
        assert create_response.status_code == 201

        # 2. Получение списка магазинов
        list_response = client.get("/api/stores")
        assert list_response.status_code == 200
        stores = list_response.json()
        assert any(store["id"] == sample_store["id"] for store in stores)

        # 3. Получение конкретного магазина
        get_response = client.get(f"/api/stores/{sample_store['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == sample_store["name"]

    def test_api_error_handling(self, client):
        """Тест обработки ошибок API"""
        # Несуществующий эндпоинт
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

        # Невалидные данные
        invalid_game = {"title": 123}  # Должно быть строкой
        response = client.post("/api/games", json=invalid_game)
        assert response.status_code == 422

    def test_cors_headers(self, client):
        """Тест CORS заголовков"""
        response = client.options("/api/games")
        assert response.status_code == 200

    def test_health_and_metrics(self, client):
        """Тест health check и метрик"""
        # Health check
        health_response = client.get("/healthz")
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "ok"

        # Метрики
        metrics_response = client.get("/metrics")
        assert metrics_response.status_code == 200
        assert "text/plain" in metrics_response.headers["content-type"]