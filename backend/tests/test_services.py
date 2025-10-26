import pytest
from unittest.mock import Mock, patch
from app.services.game_matching_service import GameMatchingService
from app.services.notification_service import NotificationService


class TestGameMatchingService:
    """Тесты сервиса сопоставления игр"""

    def test_fuzzy_matching(self):
        """Тест нечеткого сопоставления названий"""
        db_mock = Mock()
        service = GameMatchingService(db_mock)

        # Тест точного совпадения
        score1 = service.calculate_similarity("Громкое дело", "Громкое дело")
        assert score1 > 0.9

        # Тест частичного совпадения
        score2 = service.calculate_similarity("Громкое дело", "Громкое дело: Новая эра")
        assert score2 > 0.7

        # Тест разных названий
        score3 = service.calculate_similarity("Громкое дело", "Монополия")
        assert score3 < 0.3

    @patch('app.services.game_matching_service.fuzzywuzzy.fuzz.ratio')
    def test_find_matching_games(self, mock_fuzz_ratio):
        """Тест поиска подходящих игр"""
        mock_fuzz_ratio.return_value = 85

        db_mock = Mock()
        service = GameMatchingService(db_mock)

        # Мок запроса к базе данных
        mock_games = [
            Mock(title="Громкое дело", id="1"),
            Mock(title="Другая игра", id="2")
        ]
        db_mock.query.return_value.all.return_value = mock_games

        results = service.find_matching_games("Громкое дело")
        assert len(results) >= 1
        # Более детальные проверки зависят от реализации


class TestNotificationService:
    """Тесты сервиса уведомлений"""

    def test_rule_evaluation(self):
        """Тест оценки правил"""
        db_mock = Mock()
        service = NotificationService(db_mock)

        # Тестовое правило
        rule = {
            "logic": "AND",
            "conditions": [
                {"field": "price", "op": "<=", "value": 1000},
                {"field": "discount_pct", "op": ">=", "value": 20}
            ]
        }

        # Тестовое событие
        event = {
            "price": 800,
            "discount_pct": 25,
            "store_id": "test_store"
        }

        result = service.evaluate_rule(event, rule)
        assert result == True

    def test_rule_evaluation_or_logic(self):
        """Тест оценки правил с логикой ИЛИ"""
        db_mock = Mock()
        service = NotificationService(db_mock)

        rule = {
            "logic": "OR",
            "conditions": [
                {"field": "price", "op": "<=", "value": 500},
                {"field": "discount_pct", "op": ">=", "value": 30}
            ]
        }

        # Событие соответствует второму условию, но не первому
        event = {
            "price": 800,
            "discount_pct": 35,
            "store_id": "test_store"
        }

        result = service.evaluate_rule(event, rule)
        assert result == True

    @patch('app.services.notification_service.requests.post')
    def test_send_webpush_notification(self, mock_post):
        """Тест отправки Web Push уведомления"""
        mock_post.return_value.status_code = 200

        db_mock = Mock()
        service = NotificationService(db_mock)

        notification = {
            "title": "Тестовое уведомление",
            "body": "Тестовое сообщение",
            "url": "https://example.com"
        }

        subscription = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test",
            "keys": {
                "auth": "test_auth",
                "p256dh": "test_p256dh"
            }
        }

        result = service.send_webpush(notification, subscription)
        assert result is True