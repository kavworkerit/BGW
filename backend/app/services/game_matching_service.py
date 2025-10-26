"""Сервис для сопоставления игр."""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.game import Game
from fuzzywuzzy import fuzz
import re
import logging

logger = logging.getLogger(__name__)


class GameMatchingService:
    """Сервис для сопоставления названий игр с базой данных."""

    def __init__(self):
        # Слова для удаления из названий
        self.stop_words = {
            'настольная игра', 'игра', 'издание', 'база', 'делюкс', 'эксклюзив',
            'набор', 'board game', 'game', 'edition', 'deluxe', 'exclusive',
            'set', 'collection', 'коллекция', 'подарочное издание', 'gift edition'
        }

        # Символы для удаления
        self.remove_chars = '.,;:!?()[]{}"\'-_–—'

    async def match_game(self, db: Session, title: str, threshold: float = 0.75) -> Optional[Game]:
        """Найти соответствующую игру в базе данных."""
        # Нормализуем название
        normalized_title = self._normalize_title(title)

        # Ищем точные совпадения
        exact_match = self._find_exact_match(db, normalized_title)
        if exact_match:
            return exact_match

        # Ищем совпадения по синонимам
        synonym_match = self._find_synonym_match(db, normalized_title)
        if synonym_match:
            return synonym_match

        # Ищем нечеткие совпадения
        fuzzy_match = self._find_fuzzy_match(db, normalized_title, threshold)
        if fuzzy_match:
            return fuzzy_match

        # Если ничего не найдено, возвращаем None
        logger.info(f"No match found for title: {title}")
        return None

    def _normalize_title(self, title: str) -> str:
        """Нормализовать название игры."""
        # Приводим к нижнему регистру
        normalized = title.lower().strip()

        # Удаляем стоп-слова
        for stop_word in self.stop_words:
            normalized = normalized.replace(stop_word, '')

        # Удаляем лишние символы
        for char in self.remove_chars:
            normalized = normalized.replace(char, '')

        # Удаляем лишние пробелы
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        return normalized

    def _find_exact_match(self, db: Session, normalized_title: str) -> Optional[Game]:
        """Найти точное совпадение."""
        # Ищем по нормализованному названию
        games = db.query(Game).all()

        for game in games:
            game_normalized = self._normalize_title(game.title)
            if game_normalized == normalized_title:
                return game

            # Проверяем синонимы
            for synonym in game.synonyms or []:
                synonym_normalized = self._normalize_title(synonym)
                if synonym_normalized == normalized_title:
                    return game

        return None

    def _find_synonym_match(self, db: Session, normalized_title: str) -> Optional[Game]:
        """Найти совпадение по синонимам."""
        games = db.query(Game).all()

        for game in games:
            # Проверяем содержит ли название искомое слово
            if normalized_title in game.title.lower() or game.title.lower() in normalized_title:
                return game

            # Проверяем синонимы
            for synonym in game.synonyms or []:
                if (normalized_title in synonym.lower() or
                    synonym.lower() in normalized_title or
                    normalized_title == synonym.lower()):
                    return game

        return None

    def _find_fuzzy_match(self, db: Session, normalized_title: str, threshold: float) -> Optional[Game]:
        """Найти нечеткое совпадение."""
        games = db.query(Game).all()
        best_match = None
        best_score = 0

        for game in games:
            # Сравниваем с названием
            score1 = fuzz.ratio(normalized_title, self._normalize_title(game.title))
            if score1 > best_score:
                best_score = score1
                best_match = game

            # Сравниваем с синонимами
            for synonym in game.synonyms or []:
                score2 = fuzz.ratio(normalized_title, self._normalize_title(synonym))
                if score2 > best_score:
                    best_score = score2
                    best_match = game

        # Проверяем порог
        if best_score >= threshold * 100:
            logger.info(f"Fuzzy match found: {best_match.title} (score: {best_score})")
            return best_match

        return None

    async def create_suggestions(self, db: Session, title: str, limit: int = 5) -> List[Game]:
        """Создать предложения для сопоставления."""
        normalized_title = self._normalize_title(title)
        games = db.query(Game).all()

        suggestions = []
        for game in games:
            # Считаем схожесть с названием
            score1 = fuzz.ratio(normalized_title, self._normalize_title(game.title))
            max_score = score1

            # И с синонимами
            for synonym in game.synonyms or []:
                score2 = fuzz.ratio(normalized_title, self._normalize_title(synonym))
                max_score = max(max_score, score2)

            if max_score > 50:  # Порог для предложений
                suggestions.append((game, max_score))

        # Сортируем по релевантности
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return [game for game, _ in suggestions[:limit]]


game_matching_service = GameMatchingService()