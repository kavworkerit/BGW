#!/usr/bin/env python3
"""Скрипт для проверки зарегистрированных агентов."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.agents.registry import agent_registry

def test_agent_registry():
    """Проверить реестр агентов."""
    agents = agent_registry.list_agents()

    print("Зарегистрированные агенты:")
    for agent_id, agent_class in agents.items():
        print(f"  - {agent_id}: {agent_class.__name__} (тип: {agent_class.TYPE})")

    # Проверяем конкретные агенты из ТЗ
    expected_agents = [
        'HobbyGamesComingSoonAgent',
        'HobbyGamesCatalogNewAgent',
        'LavkaIgrShopAgent',
        'LavkaIgrProjectsAgent',
        'NastolPublicationsAgent',
        'NastolSpecificArticleAgent',
        'EvrikusCatalogAgent',
        'CrowdGamesAgent',
        'GagaAgent',
        'ZvezdaAgent',
        'ChooChooGamesAgent'
    ]

    print(f"\nОжидается агентов: {len(expected_agents)}")
    print("Проверка ожидаемых агентов:")

    found_count = 0
    for expected in expected_agents:
        if expected in agents:
            print(f"  ✅ {expected}")
            found_count += 1
        else:
            print(f"  ❌ {expected}")

    print(f"\nНайдено агентов: {found_count}/{len(expected_agents)}")

    if found_count == len(expected_agents):
        print("🎉 Все агенты успешно зарегистрированы!")
        return True
    else:
        print("⚠️ Некоторые агенты не найдены")
        return False

if __name__ == "__main__":
    test_agent_registry()