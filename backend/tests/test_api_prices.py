"""
Тесты для API эндпоинтов цен.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Импортируем приложение для тестов
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main import app


@pytest.fixture
def client():
    """Создание тестового клиента."""
    return TestClient(app)


@pytest.fixture
def mock_db_session():
    """Мок сессии базы данных."""
    from unittest.mock import Mock
    session = Mock()

    # Настраиваем мок для query
    mock_query = Mock()
    session.query.return_value = mock_query
    mock_query.join.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.limit.return_value = mock_query

    return session


class TestPricesAPI:
    """Тесты API эндпоинтов цен."""

    @patch('app.api.prices.get_db')
    def test_get_price_history_success(self, mock_get_db, client):
        """Успешное получение истории цен."""
        # Настраиваем моки
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Создаем мок данных
        mock_price_history = Mock()
        mock_price_history.game_id = "test-game-id"
        mock_price_history.store_id = "test-store"
        mock_price_history.observed_at = datetime.now()
        mock_price_history.price = 2999.99
        mock_price_history.currency = "RUB"

        mock_query_result = [(mock_price_history, "Test Game", "Test Store")]

        mock_db.query.return_value.join.return_value.filter.return_value\
            .order_by.return_value.limit.return_value.all.return_value = mock_query_result

        # Выполняем запрос
        response = client.get("/api/prices/")

        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['game_title'] == "Test Game"
        assert data[0]['store_name'] == "Test Store"
        assert data[0]['price'] == 2999.99

    @patch('app.api.prices.get_db')
    def test_get_price_history_with_filters(self, mock_get_db, client):
        """Получение истории цен с фильтрами."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Возвращаем пустой результат
        mock_db.query.return_value.join.return_value.filter.return_value\
            .order_by.return_value.limit.return_value.all.return_value = []

        # Выполняем запрос с фильтрами
        response = client.get("/api/prices/?game_id=test-game&store_ids=store1&store_ids=store2&days=30")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_price_history_invalid_date_format(self, client):
        """Неверный формат даты."""
        response = client.get("/api/prices/?from_date=invalid-date")
        assert response.status_code == 400
        assert "Неверный формат даты" in response.json()['detail']

    @patch('app.api.prices.get_db')
    def test_export_csv_success(self, mock_get_db, client):
        """Успешный экспорт CSV."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Создаем мок данных
        mock_price_history = Mock()
        mock_price_history.game_id = "test-game-id"
        mock_price_history.store_id = "test-store"
        mock_price_history.observed_at = datetime.now()
        mock_price_history.price = 2999.99
        mock_price_history.currency = "RUB"

        mock_query_result = [(mock_price_history, "Test Game", "Test Store")]

        mock_db.query.return_value.join.return_value.filter.return_value\
            .order_by.return_value.all.return_value = mock_query_result

        # Выполняем запрос
        response = client.get("/api/prices/export/csv")

        # Проверяем результат
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]

    @patch('app.api.prices.get_db')
    def test_get_price_stats_success(self, mock_get_db, client):
        """Успешное получение статистики цен."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Создаем мок данных
        mock_price = Mock()
        mock_price.price = 2999.99

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_price]

        # Мок для Store
        mock_store = Mock()
        mock_store.name = "Test Store"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_store

        # Выполняем запрос
        response = client.get("/api/prices/stats?game_id=test-game&days=30")

        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert data['game_id'] == 'test-game'
        assert data['period_days'] == 30
        assert data['data_points'] == 1
        assert data['min_price'] == 2999.99
        assert data['max_price'] == 2999.99
        assert data['avg_price'] == 2999.99

    @patch('app.api.prices.get_db')
    def test_get_price_stats_no_data(self, mock_get_db, client):
        """Статистика цен при отсутствии данных."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Возвращаем пустой результат
        mock_db.query.return_value.filter.return_value.all.return_value = []

        # Выполняем запрос
        response = client.get("/api/prices/stats?game_id=test-game")

        # Проверяем результат
        assert response.status_code == 200
        data = response.json()
        assert data['data_points'] == 0
        assert data['min_price'] is None
        assert data['max_price'] is None
        assert data['avg_price'] is None

    def test_get_price_stats_missing_game_id(self, client):
        """Отсутствие обязательного параметра game_id."""
        response = client.get("/api/prices/stats")
        assert response.status_code == 422  # Validation error

    @patch('app.api.prices.get_db')
    def test_get_price_stats_invalid_days(self, mock_get_db, client):
        """Неверное значение параметра days."""
        mock_db = Mock()
        mock_get_db.return_value = mock_db

        response = client.get("/api/prices/stats?game_id=test&days=1000")
        assert response.status_code == 422  # Validation error - days > 730


if __name__ == '__main__':
    pytest.main([__file__])