from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging

from app.services.llm_service import llm_service

logger = logging.getLogger(__name__)

router = APIRouter()


class LLMStatusResponse(BaseModel):
    """Ответ о статусе LLM."""
    available: bool
    url: Optional[str] = None
    models: List[str] = []
    current_model: Optional[str] = None
    error: Optional[str] = None


class LLMTestRequest(BaseModel):
    """Запрос на тестирование LLM."""
    text: str
    task: str = "extract_game_info"  # extract_game_info, normalize_title, categorize_event, suggest_synonyms


class LLMTestResponse(BaseModel):
    """Ответ от LLM теста."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


@router.get("/status", response_model=LLMStatusResponse)
async def get_llm_status():
    """Проверить статус LLM сервиса."""
    try:
        url = llm_service.base_url
        available = await llm_service.is_available()

        models = []
        current_model = None
        error = None

        if available:
            try:
                models = await llm_service.get_available_models()
                current_model = llm_service.model
            except Exception as e:
                error = str(e)
                logger.error(f"Error getting models: {e}")
        else:
            error = "LLM service not available"

        return LLMStatusResponse(
            available=available,
            url=url,
            models=models,
            current_model=current_model,
            error=error
        )

    except Exception as e:
        logger.error(f"Error checking LLM status: {e}")
        return LLMStatusResponse(
            available=False,
            error=str(e)
        )


@router.post("/test", response_model=LLMTestResponse)
async def test_llm(request: LLMTestRequest):
    """Протестировать LLM на конкретной задаче."""
    import time
    start_time = time.time()

    try:
        # Проверяем доступность
        if not await llm_service.is_available():
            return LLMTestResponse(
                success=False,
                error="LLM service not available"
            )

        # Выполняем задачу
        result = None
        task = request.task

        if task == "extract_game_info":
            result = await llm_service.extract_game_info(request.text)
        elif task == "normalize_title":
            normalized = await llm_service.normalize_game_title(request.text)
            result = {"normalized_title": normalized}
        elif task == "categorize_event":
            event_type = await llm_service.categorize_event(request.text)
            result = {"event_type": event_type}
        elif task == "suggest_synonyms":
            synonyms = await llm_service.suggest_synonyms(request.text)
            result = {"synonyms": synonyms}
        else:
            return LLMTestResponse(
                success=False,
                error=f"Unknown task: {task}"
            )

        processing_time = time.time() - start_time

        return LLMTestResponse(
            success=True,
            result=result,
            processing_time=processing_time
        )

    except Exception as e:
        logger.error(f"Error testing LLM: {e}")
        processing_time = time.time() - start_time

        return LLMTestResponse(
            success=False,
            error=str(e),
            processing_time=processing_time
        )


@router.post("/models/switch")
async def switch_model(model_name: str):
    """Переключить модель LLM."""
    try:
        if not await llm_service.is_available():
            raise HTTPException(400, "LLM service not available")

        success = await llm_service.set_model(model_name)
        if not success:
            available_models = await llm_service.get_available_models()
            raise HTTPException(
                400,
                f"Model '{model_name}' not available. Available models: {available_models}"
            )

        return {
            "success": True,
            "model": model_name,
            "message": f"Switched to model: {model_name}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        raise HTTPException(500, f"Failed to switch model: {str(e)}")


@router.post("/game/extract")
async def extract_game_info(text: str, html_fragment: str = ""):
    """Извлечь информацию об игре из текста."""
    try:
        if not await llm_service.is_available():
            raise HTTPException(400, "LLM service not available")

        result = await llm_service.extract_game_info(text, html_fragment)

        if not result:
            return {
                "success": False,
                "message": "Failed to extract game info",
                "result": None
            }

        return {
            "success": True,
            "result": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting game info: {e}")
        raise HTTPException(500, f"Failed to extract game info: {str(e)}")


@router.post("/game/normalize")
async def normalize_game_title(title: str):
    """Нормализовать название игры."""
    try:
        if not await llm_service.is_available():
            raise HTTPException(400, "LLM service not available")

        result = await llm_service.normalize_game_title(title)

        if not result:
            return {
                "success": False,
                "message": "Failed to normalize title",
                "original": title,
                "normalized": None
            }

        return {
            "success": True,
            "original": title,
            "normalized": result
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error normalizing title: {e}")
        raise HTTPException(500, f"Failed to normalize title: {str(e)}")


@router.post("/game/synonyms")
async def suggest_synonyms(title: str, description: str = ""):
    """Предложить синонимы для названия игры."""
    try:
        if not await llm_service.is_available():
            raise HTTPException(400, "LLM service not available")

        synonyms = await llm_service.suggest_synonyms(title, description)

        return {
            "success": True,
            "title": title,
            "synonyms": synonyms,
            "count": len(synonyms)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting synonyms: {e}")
        raise HTTPException(500, f"Failed to suggest synonyms: {str(e)}")


@router.post("/event/categorize")
async def categorize_event(title: str, description: str = ""):
    """Определить тип события."""
    try:
        if not await llm_service.is_available():
            raise HTTPException(400, "LLM service not available")

        event_type = await llm_service.categorize_event(title, description)

        if not event_type:
            return {
                "success": False,
                "message": "Failed to categorize event",
                "title": title,
                "event_type": None
            }

        return {
            "success": True,
            "title": title,
            "event_type": event_type
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error categorizing event: {e}")
        raise HTTPException(500, f"Failed to categorize event: {str(e)}")