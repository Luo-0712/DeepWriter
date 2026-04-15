"""
Base Retriever
==============

Base class for document retrievers.
"""

from abc import abstractmethod
from typing import List, Optional

from services.rag.components.base import BaseComponent
from services.rag.types import SearchResult


class BaseRetriever(BaseComponent):
    """
    Base class for document retrievers.

    All retrievers must implement:
    - retrieve(query, kb_name, **kwargs) -> SearchResult
    """

    name: str = "base_retriever"

    def __init__(self, kb_base_dir: Optional[str] = None, top_k: int = 5):
        super().__init__()
        self.kb_base_dir = kb_base_dir or "./data/knowledge_bases"
        self.top_k = top_k

    @abstractmethod
    async def retrieve(self, query: str, kb_name: str, **kwargs) -> SearchResult:
        """
        Retrieve documents matching the query.

        Args:
            query: Search query
            kb_name: Knowledge base name
            **kwargs: Additional options
                - top_k: Number of results to return

        Returns:
            SearchResult with matching chunks
        """
        raise NotImplementedError("Subclasses must implement retrieve()")

    async def process(self, data: str, **kwargs) -> SearchResult:
        """
        Process interface (wrapper for retrieve).

        Args:
            data: Query string
            **kwargs: Additional options including kb_name

        Returns:
            SearchResult
        """
        kb_name = kwargs.get("kb_name")
        if not kb_name:
            raise ValueError("kb_name is required for retrieval")
        return await self.retrieve(data, kb_name, **kwargs)
