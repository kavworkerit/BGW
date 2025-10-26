"""
Тесты для сервиса дедупликации событий.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.services.deduplication_service import (
    normalize_text,
    calculate_signature_hash,
    is_duplicate_event,
    create_event_with_deduplication
)


class TestTextNormalization:
    """Тесты нормализации текста."""

    def test_normalize_basic_text(self):
        """Базовая нормализация текста."""
        text = "  Настольная Игра Dune: Империум  "
        result = normalize_text(text)
        assert result == "dune империум"

    def test_normalize_removes_junk_words(self):
        """Удаление мусорных слов."""
        text = "Настольная игра deluxe издание"
        result = normalize_text(text)
        assert result == ""

    def test_normalize_handles_special_chars(self):
        """Обработка спецсимволов."""
        text = "Dune: Imperium - Deluxe Edition!"
        result = normalize_text(text)
        assert result == "dune imperium deluxe edition"

    def test_normalize_empty_text(self):
        """Пустой текст."""
        assert normalize_text("") == ""
        assert normalize_text(None) == ""

    def test_normalize_multiple_spaces(self):
        """Множественные пробелы."""
        text = "Dune    Imperium"
        result = normalize_text(text)
        assert result == "dune imperium"


class TestSignatureHash:
    """Тесты вычисления signature_hash."""

    def test_hash_consistency(self):
        """Консистентность хеша."""
        event_data = {
            'title': 'Dune: Imperium',
            'store_id': 'test_store',
            'edition': 'Deluxe',
            'price': 2999.99
        }

        hash1 = calculate_signature_hash(event_data)
        hash2 = calculate_signature_hash(event_data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex

    def test_hash_different_titles(self):
        """Разные заголовки дают разные хеши."""
        base_data = {
            'store_id': 'test_store',
            'edition': '',
            'price': 1000
        }

        hash1 = calculate_signature_hash({**base_data, 'title': 'Game 1'})
        hash2 = calculate_signature_hash({**base_data, 'title': 'Game 2'})

        assert hash1 != hash2

    def test_hash_handles_null_price(self):
        """Обработка null цены."""
        event_data = {
            'title': 'Test Game',
            'store_id': 'test',
            'edition': '',
            'price': None
        }

        hash1 = calculate_signature_hash(event_data)
        hash2 = calculate_signature_hash(event_data)

        assert hash1 == hash2

    def test_hash_rounds_price(self):
        """Округление цены."""
        base_data = {
            'title': 'Test Game',
            'store_id': 'test',
            'edition': ''
        }

        hash1 = calculate_signature_hash({**base_data, 'price': 2999.99})
        hash2 = calculate_signature_hash({**base_data, 'price': 3000.01})

        assert hash1 == hash2  # Округлится до 3000


@pytest.fixture
def mock_db_session():
    """Мок сессии базы данных."""
    from unittest.mock import Mock
    return Mock()


class TestDuplicateDetection:
    """Тесты обнаружения дубликатов."""

    def test_no_duplicate_found(self, mock_db_session):
        """Дубликат не найден."""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = is_duplicate_event(mock_db_session, "test_hash")
        assert result is None

    def test_duplicate_found(self, mock_db_session):
        """Дубликат найден."""
        from app.models.listing_event import ListingEvent

        mock_event = Mock(spec=ListingEvent)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_event

        result = is_duplicate_event(mock_db_session, "test_hash")
        assert result == mock_event

    def test_custom_hours_back(self, mock_db_session):
        """Настройка периода поиска."""
        is_duplicate_event(mock_db_session, "test_hash", hours_back=48)

        # Проверяем, что был вызван фильтр с правильными параметрами
        mock_db_session.query.return_value.filter.assert_called()


class TestEventCreationWithDeduplication:
    """Тесты создания событий с дедупликацией."""

    def test_create_new_event(self, mock_db_session):
        """Создание нового события."""
        from app.models.listing_event import ListingEvent

        # Настраиваем мок
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        event_data = {
            'title': 'New Game',
            'store_id': 'test_store',
            'price': 1000
        }

        event, is_duplicate = create_event_with_deduplication(mock_db_session, event_data)

        assert is_duplicate is False
        assert isinstance(event, ListingEvent)
        assert event.signature_hash is not None
        mock_db_session.add.assert_called_once()

    def test_detect_duplicate_event(self, mock_db_session):
        """Обнаружение дубликата."""
        from app.models.listing_event import ListingEvent

        # Настраиваем мок - возвращаем существующий дубликат
        mock_duplicate = Mock(spec=ListingEvent)
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_duplicate

        event_data = {
            'title': 'Existing Game',
            'store_id': 'test_store',
            'price': 1000
        }

        event, is_duplicate = create_event_with_deduplication(mock_db_session, event_data)

        assert is_duplicate is True
        assert event == mock_duplicate
        mock_db_session.add.assert_not_called()  # Не должен добавлять новую запись


if __name__ == '__main__':
    pytest.main([__file__])