"""
Base Parser
===========

Base class for document parsers.
"""

from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict

from services.rag.components.base import BaseComponent
from services.rag.types import Document


class BaseParser(BaseComponent):
    """
    Base class for document parsers.

    All parsers must implement:
    - parse(file_path, **kwargs) -> Document
    """

    name: str = "base_parser"

    @abstractmethod
    async def parse(self, file_path: str, **kwargs) -> Document:
        """
        Parse a document file.

        Args:
            file_path: Path to the document file
            **kwargs: Additional parsing options

        Returns:
            Parsed Document object
        """
        raise NotImplementedError("Subclasses must implement parse()")

    async def process(self, data: str, **kwargs) -> Document:
        """
        Process interface (wrapper for parse).

        Args:
            data: File path to parse
            **kwargs: Additional options

        Returns:
            Parsed Document
        """
        return await self.parse(data, **kwargs)

    def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract basic metadata from file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary of metadata
        """
        path = Path(file_path)
        return {
            "file_path": str(file_path),
            "file_name": path.name,
            "file_extension": path.suffix.lower(),
            "file_size": path.stat().st_size if path.exists() else 0,
        }
