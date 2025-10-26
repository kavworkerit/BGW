"""Реестр агентов."""
from typing import Dict, Type, Any
import importlib
import os
from pathlib import Path
from .base import BaseAgent


class AgentRegistry:
    """Реестр доступных агентов."""

    def __init__(self):
        self._agents: Dict[str, Type[BaseAgent]] = {}
        self._load_builtin_agents()

    def _load_builtin_agents(self):
        """Загрузить встроенных агентов."""
        agents_dir = Path(__file__).parent / "builtin"
        if not agents_dir.exists():
            return

        for agent_file in agents_dir.glob("*.py"):
            if agent_file.name.startswith("_"):
                continue

            module_name = f"app.agents.builtin.{agent_file.stem}"
            try:
                module = importlib.import_module(module_name)
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseAgent)
                        and attr != BaseAgent
                    ):
                        self._agents[attr_name] = attr
            except Exception as e:
                print(f"Failed to load agent {agent_file}: {e}")

    def register(self, agent_id: str, agent_class: Type[BaseAgent]):
        """Зарегистрировать агент."""
        self._agents[agent_id] = agent_class

    def get(self, agent_id: str) -> Type[BaseAgent]:
        """Получить класс агента по ID."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")
        return self._agents[agent_id]

    def list_agents(self) -> Dict[str, Type[BaseAgent]]:
        """Получить список всех агентов."""
        return self._agents.copy()


# Глобальный реестр
agent_registry = AgentRegistry()