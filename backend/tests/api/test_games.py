import pytest
from uuid import uuid4


class TestGamesAPI:
    """Тесты API для работы с играми"""

    def test_create_game(self, client, sample_game):
        """Тест создания игры"""
        # Используем уникальный BGG ID для каждого теста
        game_data = sample_game.copy()
        game_data["bgg_id"] = str(uuid4())

        response = client.post("/api/games", json=game_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == game_data["title"]
        assert "id" in data
        assert data["synonyms"] == game_data["synonyms"]

    def test_get_games(self, client, sample_game):
        """Тест получения списка игр"""
        # Сначала создадим игру с уникальным BGG ID
        game_data = sample_game.copy()
        game_data["bgg_id"] = str(uuid4())
        client.post("/api/games", json=game_data)

        # Теперь получим список
        response = client.get("/api/games")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) >= 1
        assert any(game["title"] == game_data["title"] for game in data["items"])

    def test_get_game_by_id(self, client, sample_game):
        """Тест получения игры по ID"""
        # Создаем игру с уникальным BGG ID
        game_data = sample_game.copy()
        game_data["bgg_id"] = str(uuid4())
        create_response = client.post("/api/games", json=game_data)
        game_id = create_response.json()["id"]

        # Получаем по ID
        response = client.get(f"/api/games/{game_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == game_id
        assert data["title"] == game_data["title"]

    def test_get_nonexistent_game(self, client):
        """Тест получения несуществующей игры"""
        fake_id = uuid4()
        response = client.get(f"/api/games/{fake_id}")
        assert response.status_code == 404

    def test_update_game(self, client, sample_game):
        """Тест обновления игры"""
        # Создаем игру с уникальным BGG ID
        game_data = sample_game.copy()
        game_data["bgg_id"] = str(uuid4())
        create_response = client.post("/api/games", json=game_data)
        game_id = create_response.json()["id"]

        # Обновляем
        update_data = {"title": "Обновленное название игры"}
        response = client.put(f"/api/games/{game_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["id"] == game_id

    def test_delete_game(self, client, sample_game):
        """Тест удаления игры"""
        # Создаем игру с уникальным BGG ID
        game_data = sample_game.copy()
        game_data["bgg_id"] = str(uuid4())
        create_response = client.post("/api/games", json=game_data)
        game_id = create_response.json()["id"]

        # Удаляем
        response = client.delete(f"/api/games/{game_id}")
        assert response.status_code == 200

        # Проверяем, что игра удалена
        get_response = client.get(f"/api/games/{game_id}")
        assert get_response.status_code == 404

    def test_create_game_validation_error(self, client):
        """Тест валидации при создании игры"""
        invalid_game = {"title": ""}  # Пустое название
        response = client.post("/api/games", json=invalid_game)
        assert response.status_code == 422