"""Unit тесты для API эндпоинтов игр с использованием mock объектов"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.models.game import Game
from app.schemas.game import GameCreate, GameUpdate


class TestGamesAPIUnit:
    """Unit тесты для API эндпоинтов игр"""

    def setup_method(self):
        """Настройка для каждого теста"""
        self.client = TestClient(app)
        self.game_id = str(uuid4())
        self.sample_game_data = {
            "title": "Тестовая игра",
            "synonyms": ["Тест игра"],
            "bgg_id": "12345",
            "publisher": "Тестовый издатель",
            "tags": ["стратегия"],
            "description": "Описание тестовой игры",
            "min_players": 2,
            "max_players": 4,
            "min_playtime": 30,
            "max_playtime": 60,
            "language": "RU",
            "complexity": 3.5
        }

    @patch('app.api.games.game_crud.create')
    @patch('app.api.games.get_db')
    def test_create_game_success(self, mock_get_db, mock_crud_create):
        """Тест успешного создания игры"""
        # Настройка mock
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        created_game = Game(id=uuid4(), **self.sample_game_data)
        mock_crud_create.return_value = created_game

        # Выполнение запроса
        response = self.client.post("/api/games", json=self.sample_game_data)

        # Проверки
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == self.sample_game_data["title"]
        assert data["publisher"] == self.sample_game_data["publisher"]
        mock_crud_create.assert_called_once_with(mock_db, obj_in=GameCreate(**self.sample_game_data))

    @patch('app.api.games.game_crud.create')
    @patch('app.api.games.get_db')
    def test_create_game_duplicate_bgg_id(self, mock_get_db, mock_crud_create):
        """Тест создания игры с дубликатом BGG ID"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Проверка на дубликат в самом API
        mock_existing_game = Game(id=uuid4(), title="Существующая игра", bgg_id="12345")
        mock_db.query.return_value.filter.return_value.first.return_value = mock_existing_game

        response = self.client.post("/api/games", json=self.sample_game_data)

        assert response.status_code == 400
        assert "таким BGG ID уже существует" in response.json()["detail"]

    @patch('app.api.games.game_crud.get')
    @patch('app.api.games.get_db')
    def test_get_game_by_id_success(self, mock_get_db, mock_crud_get):
        """Тест успешного получения игры по ID"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        game = Game(id=uuid4(), **self.sample_game_data)
        mock_crud_get.return_value = game

        response = self.client.get(f"/api/games/{self.game_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == self.sample_game_data["title"]
        mock_crud_get.assert_called_once_with(mock_db, self.game_id)

    @patch('app.api.games.game_crud.get')
    @patch('app.api.games.get_db')
    def test_get_game_not_found(self, mock_get_db, mock_crud_get):
        """Тест получения несуществующей игры"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        mock_crud_get.return_value = None

        response = self.client.get(f"/api/games/{self.game_id}")

        assert response.status_code == 404
        assert "Игра не найдена" in response.json()["detail"]

    @patch('app.api.games.game_crud.update')
    @patch('app.api.games.game_crud.get')
    @patch('app.api.games.get_db')
    def test_update_game_success(self, mock_get_db, mock_crud_get, mock_crud_update):
        """Тест успешного обновления игры"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        existing_game = Game(id=uuid4(), **self.sample_game_data)
        mock_crud_get.return_value = existing_game

        updated_game_data = {**self.sample_game_data, "title": "Обновленное название"}
        updated_game = Game(id=existing_game.id, **updated_game_data)
        mock_crud_update.return_value = updated_game

        update_data = {"title": "Обновленное название"}
        response = self.client.put(f"/api/games/{self.game_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Обновленное название"
        mock_crud_update.assert_called_once()

    @patch('app.api.games.game_crud.get')
    @patch('app.api.games.game_crud.remove')
    @patch('app.api.games.get_db')
    @patch('app.api.games.db')
    def test_delete_game_success(self, mock_db_query, mock_get_db, mock_crud_get, mock_crud_remove):
        """Тест успешного удаления игры"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        game = Game(id=uuid4(), **self.sample_game_data)
        mock_crud_get.return_value = game

        # Нет связанных событий
        mock_db_query.query.return_value.filter.return_value.count.return_value = 0

        response = self.client.delete(f"/api/games/{self.game_id}")

        assert response.status_code == 200
        assert "Игра удалена" in response.json()["message"]
        mock_crud_remove.assert_called_once_with(mock_db, id=self.game_id)

    @patch('app.api.games.game_crud.get')
    @patch('app.api.games.get_db')
    @patch('app.api.games.db')
    def test_delete_game_with_events(self, mock_db_query, mock_get_db, mock_crud_get):
        """Тест удаления игры со связанными событиями"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        game = Game(id=uuid4(), **self.sample_game_data)
        mock_crud_get.return_value = game

        # Есть связанные события
        mock_db_query.query.return_value.filter.return_value.count.return_value = 5

        response = self.client.delete(f"/api/games/{self.game_id}")

        assert response.status_code == 400
        assert "Нельзя удалить игру" in response.json()["detail"]
        assert "5 связанных событий" in response.json()["detail"]

    @patch('app.api.games.PaginationHelper.get_paginated_results')
    @patch('app.api.games.db')
    @patch('app.api.games.get_db')
    def test_get_games_list_success(self, mock_get_db, mock_db, mock_pagination):
        """Тест успешного получения списка игр"""
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        # Mock запроса
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query

        # Mock пагинации
        games = [
            Game(id=uuid4(), title="Игра 1"),
            Game(id=uuid4(), title="Игра 2")
        ]
        mock_pagination.return_value = (games, 2)

        response = self.client.get("/api/games")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @patch('app.api.games.game_matching_service.create_suggestions')
    @patch('app.api.games.get_db')
    def test_match_games_success(self, mock_get_db, mock_matching_service):
        """Тест поиска подходящих игр"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        suggested_games = [
            Game(id=uuid4(), title="Громкое дело", publisher="Правильные игры"),
            Game(id=uuid4(), title="Громкое дело: Расширение", publisher="Правильные игры")
        ]
        mock_matching_service.return_value = suggested_games

        response = self.client.post("/api/games/match?title=Громкое дело")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("title" in game for game in data)
        mock_matching_service.assert_called_once_with(mock_db, "Громкое дело", 5)

    @patch('app.api.games.db')
    @patch('app.api.games.get_db')
    def test_get_games_stats_success(self, mock_get_db, mock_db):
        """Тест получения статистики по играм"""
        mock_db_session = Mock()
        mock_get_db.return_value = mock_db_session

        # Mock статистики
        mock_db_session.query.return_value.count.return_value = 100
        mock_db_session.query.return_value.filter.return_value.count.return_value = 80
        mock_db_session.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
            ("Правильные игры", 15),
            ("Hobby Games", 12)
        ]
        mock_db_session.query.return_value.group_by.return_value.order_by.return_value.all.return_value = [
            ("RU", 70),
            ("EN", 30)
        ]

        response = self.client.get("/api/games/stats/summary")

        assert response.status_code == 200
        data = response.json()
        assert data["total_games"] == 100
        assert data["bgg_linked_games"] == 80
        assert data["bgg_coverage_percent"] == 80.0
        assert len(data["top_publishers"]) == 2
        assert len(data["languages"]) == 2

    def test_create_game_validation_error(self):
        """Тест валидации при создании игры"""
        invalid_data = {
            "title": "",  # Пустое название
            "min_players": -1,  # Отрицательное значение
            "max_players": 0,   # Нулевое значение
            "complexity": 6.0   # Слишком высокое значение
        }

        response = self.client.post("/api/games", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_update_game_validation_error(self):
        """Тест валидации при обновлении игры"""
        invalid_data = {
            "min_players": -5,
            "complexity": -1.0
        }

        response = self.client.put(f"/api/games/{self.game_id}", json=invalid_data)

        assert response.status_code == 422  # Validation error

    @patch('app.api.games.game_crud.create')
    @patch('app.api.games.get_db')
    def test_create_games_batch_success(self, mock_get_db, mock_crud_create):
        """Тест создания нескольких игр"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        created_games = [
            Game(id=uuid4(), title="Игра 1", publisher="Издатель 1"),
            Game(id=uuid4(), title="Игра 2", publisher="Издатель 2")
        ]
        mock_crud_create.side_effect = created_games

        games_data = [
            {"title": "Игра 1", "publisher": "Издатель 1"},
            {"title": "Игра 2", "publisher": "Издатель 2"}
        ]

        response = self.client.post("/api/games/batch", json=games_data)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Игра 1"
        assert data[1]["title"] == "Игра 2"

    @patch('app.api.games.game_crud.get')
    @patch('app.api.games.get_db')
    @patch('app.api.games.db')
    def test_get_game_events_success(self, mock_db_query, mock_get_db, mock_crud_get):
        """Тест получения событий игры"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        game = Game(id=uuid4(), **self.sample_game_data)
        mock_crud_get.return_value = game

        # Mock событий
        from app.models.listing_event import ListingEvent
        from datetime import datetime

        mock_event = Mock(spec=ListingEvent)
        mock_event.id = uuid4()
        mock_event.kind.value = "release"
        mock_event.title = "Событие игры"
        mock_event.price = 1999.99
        mock_event.currency = "RUB"
        mock_event.discount_pct = 10.0
        mock_event.in_stock = True
        mock_event.store_id = "test_store"
        mock_event.url = "https://example.com"
        mock_event.created_at = datetime.utcnow()

        mock_db_query.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_event]

        response = self.client.get(f"/api/games/{self.game_id}/events")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Событие игры"
        assert data[0]["price"] == 1999.99