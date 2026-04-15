"""
Base Indexer
============

Base class for document indexers.
"""

from abc import abstractmethod
from typing import List, Optional

from services.rag.components.base import BaseComponent
from services.rag.types import Document, Chunk


class BaseIndexer(BaseComponent):
    """
    Base class for document indexers.

    All indexers must implement:
    - index(documents, **kwargs) -> bool
    - add_documents(documents, **kwargs) -> bool
    - delete(kb_name, **kwargs) -> bool
    """

    name: str = "base_indexer"

    def __init__(self, kb_base_dir: Optional[str] = None):
        super().__init__()
        self.kb_base_dir = kb_base_dir or "./data/knowledge_bases"

    @abstractmethod
    async def index(self, kb_name: str, documents: List[Document], **kwargs) -> bool:
        """
        Index documents into a knowledge base.

        Args:
            kb_name: Knowledge base name
            documents: List of documents to index
            **kwargs: Additional options

        Returns:
            True if successful
        """
        raise NotImplementedError("Subclasses must implement index()")

    @abstractmethod
    async def add_documents(self, kb_name: str, documents: List[Document], **kwargs) -> bool:
        """
        Add documents to an existing knowledge base.

        Args:
            kb_name: Knowledge base name
            documents: List of documents to add
            **kwargs: Additional options

        Returns:
            True if successful
        """
        raise NotImplementedError("Subclasses must implement add_documents()")

    @abstractmethod
    async def delete(self, kb_name: str, **kwargs) -> bool:
        """
        Delete a knowledge base.

        Args:
            kb_name: Knowledge base name
            **kwargs: Additional options

        Returns:
            True if successful
        """
        raise NotImplementedError("Subclasses must implement delete()")

    async def process(self, data: tuple, **kwargs) -> bool:
        """
        Process interface.

        Args:
            data: Tuple of (kb_name, documents)
            **kwargs: Additional options

        Returns:
            True if successful
        """
        kb_name, documents = data
        return await self.index(kb_name, documents, **kwargs)
