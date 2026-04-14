from typing import Optional, Type

from .base import BaseAgent


class AgentRegistry:
    _agents: dict[str, Type[BaseAgent]] = {}

    @classmethod
    def register(cls, name: str) -> callable:
        def decorator(agent_class: Type[BaseAgent]) -> Type[BaseAgent]:
            cls._agents[name] = agent_class
            return agent_class

        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseAgent]]:
        return cls._agents.get(name)

    @classmethod
    def list_agents(cls) -> list[str]:
        return list(cls._agents.keys())

    @classmethod
    def create(cls, name: str, *args, **kwargs) -> Optional[BaseAgent]:
        agent_class = cls.get(name)
        if agent_class:
            return agent_class(*args, **kwargs)
        return None
