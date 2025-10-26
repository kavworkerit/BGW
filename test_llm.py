#!/usr/bin/env python3
"""Скрипт для проверки LLM интеграции с Ollama."""

import asyncio
import sys
import os

# Добавляем путь к бэкенду
sys.path.append('/mnt/c/Projects/BGW/backend')

from app.services.llm_service import llm_service


async def test_llm_connection():
    """Тест подключения к Ollama."""
    print("🔍 Проверка подключения к Ollama...")

    available = await llm_service.is_available()
    url = llm_service.base_url

    print(f"URL: {url}")
    print(f"Доступность: {'✅ Доступен' if available else '❌ Недоступен'}")

    if not available:
        return False

    return True


async def test_available_models():
    """Тест получения доступных моделей."""
    print("\n📋 Получение списка моделей...")

    try:
        models = await llm_service.get_available_models()
        current_model = llm_service.model

        print(f"Текущая модель: {current_model}")
        print(f"Доступные модели ({len(models)}):")
        for model in models:
            status = "🔸" if model == current_model else "  "
            print(f"{status} {model}")

        return models
    except Exception as e:
        print(f"❌ Ошибка получения моделей: {e}")
        return []


async def test_extract_game_info():
    """Тест извлечения информации об игре."""
    print("\n🎮 Тест извлечения информации об игре...")

    test_text = """
    🔥 Громкое дело - Новая настольная игра уже в продаже!

    Цена: 2 500 ₽
    Скидка 20% до конца недели!

    Издатель: Правильные игры
    В наличии: ✅
    """

    try:
        result = await llm_service.extract_game_info(test_text)
        if result:
            print("✅ Успешно извлечена информация:")
            for key, value in result.items():
                print(f"  {key}: {value}")
            return True
        else:
            print("❌ Не удалось извлечь информацию")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


async def test_normalize_title():
    """Тест нормализации названий."""
    print("\n📝 Тест нормализации названий...")

    test_titles = [
        "Громкое дело. Настольная игра",
        "Dune: Imperium – Базовая игра",
        "Монополия. Новое издание 2024"
    ]

    success_count = 0
    for title in test_titles:
        try:
            result = await llm_service.normalize_game_title(title)
            if result:
                print(f"✅ '{title}' -> '{result}'")
                success_count += 1
            else:
                print(f"❌ '{title}' -> [не удалось]")
        except Exception as e:
            print(f"❌ '{title}' -> ошибка: {e}")

    return success_count == len(test_titles)


async def test_categorize_event():
    """Тест категоризации событий."""
    print("\n🏷️ Тест категоризации событий...")

    test_events = [
        ("🎉 Анонс: Громкое дело 2", ""),
        ("📦 Открыты предзаказы на Dune: Imperium", ""),
        ("🚀 В продаже: новая игра от Cosmic Games", ""),
        ("💰 Скидка 30% на все игры!", "")
    ]

    success_count = 0
    for title, description in test_events:
        try:
            result = await llm_service.categorize_event(title, description)
            if result:
                print(f"✅ '{title}' -> {result}")
                success_count += 1
            else:
                print(f"❌ '{title}' -> [не удалось]")
        except Exception as e:
            print(f"❌ '{title}' -> ошибка: {e}")

    return success_count == len(test_events)


async def test_suggest_synonyms():
    """Тест генерации синонимов."""
    print("\n🔄 Тест генерации синонимов...")

    test_title = "Громкое дело"
    test_description = "Детективная настольная игра о расследовании громких преступлений"

    try:
        synonyms = await llm_service.suggest_synonyms(test_title, test_description)
        if synonyms:
            print(f"✅ Синонимы для '{test_title}':")
            for i, synonym in enumerate(synonyms, 1):
                print(f"  {i}. {synonym}")
            return True
        else:
            print(f"❌ Не удалось сгенерировать синонимы для '{test_title}'")
            return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


async def run_all_tests():
    """Запустить все тесты."""
    print("🚀 Запуск тестов LLM интеграции с Ollama")
    print("=" * 50)

    # Тест подключения
    if not await test_llm_connection():
        print("\n❌ Ollama недоступен. Проверьте, что:")
        print("  1. Ollama установлен и запущен")
        print("  2. Адрес http://host.docker.internal:11434 доступен")
        print("  3. В Ollama загружена хотя бы одна модель")
        return False

    # Тест моделей
    models = await test_available_models()
    if not models:
        print("❌ Нет доступных моделей. Загрузите модель в Ollama:")
        print("  ollama pull llama2")
        print("  ollama pull mistral")
        return False

    # Тесты функциональности
    tests = [
        ("Извлечение информации", test_extract_game_info),
        ("Нормализация названий", test_normalize_title),
        ("Категоризация событий", test_categorize_event),
        ("Генерация синонимов", test_suggest_synonyms)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Тест '{test_name}' завершился с ошибкой: {e}")

    # Итоги
    print("\n" + "=" * 50)
    print(f"📊 Результаты тестов: {passed}/{total} пройдено")

    if passed == total:
        print("🎉 Все тесты пройдены! LLM интеграция работает корректно.")
        return True
    else:
        print("⚠️ Некоторые тесты не пройдены. Проверьте настройки.")
        return False


if __name__ == "__main__":
    asyncio.run(run_all_tests())