"""Тесты базовых моделей с использованием mock UUID"""
import pytest
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import BaseModel
from app.models.game import Game


class TestBaseModel:
    """Тесты базовой модели с UUID"""

    def test_uuid_creation(self):
        """Тест создания UUID"""
        test_uuid = uuid4()
        assert test_uuid is not None
        assert str(test_uuid) is not None

    def test_game_model_creation(self):
        """Тест создания модели Game без использования базы данных"""
        # Создаем игру без сохранения в БД
        game_data = {
            "title": "Тестовая игра",
            "bgg_id": "12345",
            "publisher": "Тестовый издатель",
            "synonyms": ["Тест игра"],
            "tags": ["тест", "игра"]
        }

        # Проверяем, что модель можно инстанциировать
        game = Game(**game_data)
        assert game.title == "Тестовая игра"
        assert game.bgg_id == "12345"
        assert game.publisher == "Тестовый издатель"

    def test_game_repr(self):
        """Тест строкового представления игры"""
        game = Game(title="Тестовая игра", publisher="Тестовый издатель")
        repr_str = repr(game)
        assert "Тестовая игра" in repr_str
        assert "Тестовый издатель" in repr_str