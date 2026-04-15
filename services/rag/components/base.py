"""
Base Component
==============

Base classes and protocols for RAG components.
"""

from typing import Any, Protocol, runtime_checkable
from abc import ABC, abstractmethod
import logging


@runtime_checkable
class Component(Protocol):
    """
    Base protocol for all RAG components.

    All components must implement:
    - name: str - Component identifier
    - process(data, **kwargs) -> Any - Process input data
    """

    name: str

    async def process(self, data: Any, **kwargs) -> Any:
        """
        Process input data.

        Args:
            data: Input data to process
            **kwargs: Additional arguments

        Returns:
            Processed output
        """
        ...


class BaseComponent(ABC):
    """
    Base class with common functionality for components.

    Provides:
    - Logger initialization
    - Default name from class name
    """

    name: str = "base"

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def process(self, data: Any, **kwargs) -> Any:
        """
        Process input data.

        Override this method in subclasses.

        Args:
            data: Input data to process
            **kwargs: Additional arguments

        Returns:
            Processed output
        """
        raise NotImplementedError("Subclasses must implement process()")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
