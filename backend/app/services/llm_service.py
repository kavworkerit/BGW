"""Сервис для работы с LLM (Ollama)."""
import json
import httpx
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Сервис для взаимодействия с Ollama LLM."""

    def __init__(self):
        self.base_url = settings.OLLAMA_URL
        self.model = "llama2"  # модель по умолчанию
        self.timeout = 30.0

    async def is_available(self) -> bool:
        """Проверить доступность Ollama."""
        if not self.base_url:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            return False

    async def extract_game_info(self, text: str, html_fragment: str = "") -> Optional[Dict[str, Any]]:
        """Извлечь информацию об игре из текста с помощью LLM."""
        if not await self.is_available():
            return None

        prompt = f"""
Проанализируй текст и извлеки информацию о настольной игре. Ответ в формате JSON.

Текст:
---
{text}

{html_fragment}
---

Извлеки следующие поля:
- title: название игры
- kind: тип события (announce/preorder/release/discount/price)
- price_rub: цена в рублях (число)
- discount_pct: скидка в процентах (число)
- in_stock: в наличии (true/false)
- edition: издание
- publisher: издатель

Если какая-то информация отсутствует, поставь null.

Пример ответа:
{{"title": "Громкое дело", "kind": "release", "price_rub": 2500, "discount_pct": null, "in_stock": true, "edition": "базовое", "publisher": "Правильные игры"}}
"""

        try:
            result = await self._call_llm(prompt)
            if result:
                return self._parse_json_response(result)
        except Exception as e:
            logger.error(f"Error extracting game info: {e}")

        return None

    async def normalize_game_title(self, title: str) -> Optional[str]:
        """Нормализовать название игры с помощью LLM."""
        if not await self.is_available():
            return None

        prompt = f"""
Приведи название настольной игры к стандартному виду. Убери лишние слова типа "настольная игра", "издание", "база".
Исправь опечатки. Если это локализация, укажи оригинальное название через косую черту.

Название: {title}

Ответ только нормализованное название, без объяснений.

Примеры:
- "Громкое дело. Настольная игра" -> "Громкое дело"
- "Dune: Imperium – Базовая игра" -> "Dune: Imperium"
- "Монополия. Новое издание" -> "Монополия"
"""

        try:
            result = await self._call_llm(prompt)
            if result:
                return result.strip().strip('"').strip("'")
        except Exception as e:
            logger.error(f"Error normalizing title: {e}")

        return None

    async def suggest_synonyms(self, title: str, description: str = "") -> List[str]:
        """Предложить синонимы для названия игры."""
        if not await self.is_available():
            return []

        prompt = f"""
Придумай 5-7 синонимов и вариантов названия для настольной игры. Включи возможные сокращения, альтернативные названия, локализации.

Название: {title}
Описание: {description}

Ответ в формате JSON списка строк:
["синоним1", "синоним2", "синоним3"]
"""

        try:
            result = await self._call_llm(prompt)
            if result:
                synonyms = self._parse_json_response(result)
                if isinstance(synonyms, list):
                    return [s for s in synonyms if s and isinstance(s, str)]
        except Exception as e:
            logger.error(f"Error suggesting synonyms: {e}")

        return []

    async def categorize_event(self, title: str, description: str = "") -> Optional[str]:
        """Определить тип события."""
        if not await self.is_available():
            return None

        prompt = f"""
Определи тип события по названию и описанию. Возможные типы:
- announce: анонс игры
- preorder: открытие предзаказов
- release: релиз, поступление в продажу
- discount: скидка, акция
- price: информация о цене без скидки

Название: {title}
Описание: {description}

Ответ только одно слово тип события (announce/preorder/release/discount/price).
"""

        try:
            result = await self._call_llm(prompt)
            if result:
                event_type = result.strip().lower()
                valid_types = ["announce", "preorder", "release", "discount", "price"]
                if event_type in valid_types:
                    return event_type
        except Exception as e:
            logger.error(f"Error categorizing event: {e}")

        return None

    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Вызвать LLM модель."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # низкая температура для более детерминированных ответов
                            "top_p": 0.9,
                            "max_tokens": 500
                        }
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("response")
                else:
                    logger.error(f"LLM API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return None

    def _parse_json_response(self, response: str) -> Optional[Any]:
        """Распарсить JSON ответ от LLM."""
        try:
            # Ищем JSON в ответе
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Пробуем распарсить весь ответ
                return json.loads(response)

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.debug(f"Response was: {response}")
            return None

    async def get_available_models(self) -> List[str]:
        """Получить список доступных моделей."""
        if not await self.is_available():
            return []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = [model["name"] for model in data.get("models", [])]
                    return models
        except Exception as e:
            logger.error(f"Error getting models: {e}")

        return []

    async def set_model(self, model_name: str) -> bool:
        """Установить модель по умолчанию."""
        available_models = await self.get_available_models()
        if model_name in available_models:
            self.model = model_name
            return True
        return False


# Глобальный экземпляр сервиса
llm_service = LLMService()