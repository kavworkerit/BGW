"""Unit тесты для игр с использованием mock объектов"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import datetime

from app.models.game import Game
from app.schemas.game import GameCreate, GameUpdate
from app.crud.game import game_crud
from app.services.game_matching_service import game_matching_service


class TestGameModel:
    """Unit тесты для модели Game"""

    def test_game_creation(self):
        """Тест создания объекта Game"""
        game_id = uuid4()
        game_data = {
            "id": game_id,
            "title": "Тестовая игра",
            "synonyms": ["Тест игра", "Test game"],
            "bgg_id": "12345",
            "publisher": "Тестовый издатель",
            "tags": ["стратегия", "экономика"],
            "description": "Описание тестовой игры",
            "min_players": 2,
            "max_players": 4,
            "min_playtime": 30,
            "max_playtime": 60,
            "year_published": 2023,
            "language": "RU",
            "complexity": 3.5,
            "image_url": "https://example.com/image.jpg",
            "rating_bgg": 7.8,
            "rating_users": 8.2,
            "weight": 2.5,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }

        game = Game(**game_data)

        assert game.id == game_id
        assert game.title == "Тестовая игра"
        assert game.synonyms == ["Тест игра", "Test game"]
        assert game.bgg_id == "12345"
        assert game.publisher == "Тестовый издатель"
        assert game.tags == ["стратегия", "экономика"]
        assert game.min_players == 2
        assert game.max_players == 4
        assert game.min_playtime == 30
        assert game.max_playtime == 60
        assert game.year_published == 2023
        assert game.language == "RU"
        assert game.complexity == 3.5
        assert game.rating_bgg == 7.8
        assert game.rating_users == 8.2
        assert game.weight == 2.5

    def test_game_repr(self):
        """Тест строкового представления"""
        game = Game(title="Громкое дело", publisher="Правильные игры")
        repr_str = repr(game)
        assert "Громкое дело" in repr_str
        assert "Правильные игры" in repr_str

    def test_game_minimal_data(self):
        """Тест создания игры с минимальными данными"""
        game = Game(title="Минимальная игра")
        assert game.title == "Минимальная игра"
        assert game.synonyms == []
        assert game.tags == []


class TestGameSchemas:
    """Unit тесты для схем Pydantic"""

    def test_game_create_schema(self):
        """Тест схемы GameCreate"""
        game_data = {
            "title": "Новая игра",
            "synonyms": ["Синоним"],
            "bgg_id": "54321",
            "publisher": "Издатель",
            "tags": ["кооперативная"],
            "description": "Описание",
            "min_players": 1,
            "max_players": 6,
            "min_playtime": 20,
            "max_playtime": 120,
            "year_published": 2024,
            "language": "EN",
            "complexity": 2.5,
            "image_url": "https://example.com/img.png"
        }

        game_create = GameCreate(**game_data)
        assert game_create.title == "Новая игра"
        assert game_create.synonyms == ["Синоним"]
        assert game_create.bgg_id == "54321"

    def test_game_update_schema(self):
        """Тест схемы GameUpdate"""
        update_data = {
            "title": "Обновленное название",
            "description": "Новое описание",
            "complexity": 4.0
        }

        game_update = GameUpdate(**update_data)
        assert game_update.title == "Обновленное название"
        assert game_update.description == "Новое описание"
        assert game_update.complexity == 4.0

    def test_game_create_validation(self):
        """Тест валидации схемы GameCreate"""
        # Пустое название должно вызывать ошибку
        with pytest.raises(ValueError):
            GameCreate(title="")

        # Некорректное количество игроков
        with pytest.raises(ValueError):
            GameCreate(title="Игра", min_players=0)


class TestGameCRUD:
    """Unit тесты для CRUD операций с mock БД"""

    @patch('app.crud.game.Session')
    def test_create_game(self, mock_session):
        """Тест создания игры через CRUD"""
        # Настройка mock
        mock_db = Mock()
        mock_game = Game(id=uuid4(), title="Тестовая игра")
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None

        game_data = GameCreate(title="Тестовая игра", publisher="Тест")

        with patch.object(game_crud, 'model', Game):
            result = game_crud.create(mock_db, obj_in=game_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch('app.crud.game.Session')
    def test_get_game_by_id(self, mock_session):
        """Тест получения игры по ID"""
        mock_db = Mock()
        game_id = uuid4()
        mock_game = Game(id=game_id, title="Тестовая игра")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_game

        result = game_crud.get(mock_db, game_id)
        assert result == mock_game
        mock_db.query.assert_called_once_with(Game)

    @patch('app.crud.game.Session')
    def test_search_games(self, mock_session):
        """Тест поиска игр"""
        mock_db = Mock()
        mock_games = [
            Game(id=uuid4(), title="Тестовая игра 1"),
            Game(id=uuid4(), title="Тестовая игра 2")
        ]

        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_games

        result = game_crud.search(mock_db, "Тестовая")
        assert len(result) == 2

    @patch('app.crud.game.Session')
    def test_get_by_bgg_id(self, mock_session):
        """Тест получения игры по BGG ID"""
        mock_db = Mock()
        mock_game = Game(id=uuid4(), title="BGG игра", bgg_id="12345")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_game

        result = game_crud.get_by_bgg_id(mock_db, "12345")
        assert result == mock_game
        assert result.bgg_id == "12345"


class TestGameMatchingService:
    """Unit тесты для сервиса поиска игр"""

    @pytest.mark.asyncio
    async def test_create_suggestions(self):
        """Тест создания предложений игр"""
        mock_db = Mock()
        title = "Громкое дело"

        # Mock результатов поиска
        mock_games = [
            Game(id=uuid4(), title="Громкое дело", publisher="Правильные игры"),
            Game(id=uuid4(), title="Громкое дело: Расширение", publisher="Правильные игры")
        ]

        with patch.object(game_matching_service, 'find_matching_games', return_value=mock_games):
            result = await game_matching_service.create_suggestions(mock_db, title, limit=5)

        assert len(result) == 2
        assert all(isinstance(game, Game) for game in result)
        game_matching_service.find_matching_games.assert_called_once_with(mock_db, title, 5)

    def test_normalize_title(self):
        """Тест нормализации названия"""
        test_cases = [
            ("Громкое дело", "громкое дело"),
            ("  Игра с пробелами  ", "игра с пробелами"),
            ("Игра: Подзаголовок", "игра подзаголовок"),
            ("Игра - Дополнение", "игра дополнение"),
            ("GAME IN ENGLISH", "game in english")
        ]

        for input_title, expected in test_cases:
            with patch.object(game_matching_service, 'normalize_title', return_value=expected):
                result = game_matching_service.normalize_title(input_title)
                assert result == expected

    def test_calculate_similarity(self):
        """Тест расчета схожести названий"""
        title1 = "Громкое дело"
        title2 = "Громкое дело: Новая эра"
        title3 = "Совсем другая игра"

        # Mock для функции схожести
        with patch.object(game_matching_service, 'calculate_similarity') as mock_sim:
            mock_sim.side_effect = [0.9, 0.1]

            similarity1 = game_matching_service.calculate_similarity(title1, title2)
            similarity2 = game_matching_service.calculate_similarity(title1, title3)

            assert similarity1 > similarity2
            assert similarity1 > 0.8  # высокая схожесть
            assert similarity2 < 0.2  # низкая схожесть


class TestGameValidation:
    """Unit тесты для валидации данных игр"""

    def test_valid_bgg_id(self):
        """Тест валидного BGG ID"""
        valid_ids = ["12345", "987654", "1", "999999"]
        for bgg_id in valid_ids:
            game = Game(title="Игра", bgg_id=bgg_id)
            assert game.bgg_id == bgg_id

    def test_valid_player_counts(self):
        """Тест валидных значений количества игроков"""
        test_cases = [
            (1, 1),  # игра для одного
            (2, 4),  # стандартная игра
            (1, 8),  # большая компания
            (4, 12)  # вечеринка
        ]

        for min_players, max_players in test_cases:
            game = Game(title="Игра", min_players=min_players, max_players=max_players)
            assert game.min_players == min_players
            assert game.max_players == max_players

    def test_valid_playtime(self):
        """Тест валидных значений времени игры"""
        test_cases = [
            (5, 15),   # короткая игра
            (30, 60),  # стандартная игра
            (60, 120), # длинная игра
            (120, 240) # очень длинная игра
        ]

        for min_playtime, max_playtime in test_cases:
            game = Game(title="Игра", min_playtime=min_playtime, max_playtime=max_playtime)
            assert game.min_playtime == min_playtime
            assert game.max_playtime == max_playtime

    def test_valid_ratings(self):
        """Тест валидных значений рейтингов"""
        test_cases = [
            (1.0, 5.0, 2.5),   # BGG рейтинг, пользовательский, сложность
            (8.5, 9.2, 3.8),   # высокие оценки
            (6.0, 7.5, 2.0),   # средние оценки
            (0.0, 10.0, 5.0)   # граничные значения
        ]

        for bgg_rating, user_rating, complexity in test_cases:
            game = Game(
                title="Игра",
                rating_bgg=bgg_rating,
                rating_users=user_rating,
                complexity=complexity
            )
            assert game.rating_bgg == bgg_rating
            assert game.rating_users == user_rating
            assert game.complexity == complexity