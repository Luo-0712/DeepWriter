"""
Base Chunker
============

Base class for text chunkers.
"""

from abc import abstractmethod
from typing import List 

from services.rag.components.base import BaseComponent
from services.rag.types import Document, Chunk


class BaseChunker(BaseComponent):
    """
    Base class for text chunkers.

    All chunkers must implement:
    - chunk(document, **kwargs) -> List[Chunk]
    """

    name: str = "base_chunker"

    @abstractmethod
    async def chunk(self, document: Document, **kwargs) -> List[Chunk]:
        """
        Split a document into chunks.

        Args:
            document: Document to chunk
            **kwargs: Additional chunking options

        Returns:
            List of Chunk objects
        """
        raise NotImplementedError("Subclasses must implement chunk()")

    async def process(self, data: Document, **kwargs) -> List[Chunk]:
        """
        Process interface (wrapper for chunk).

        Args:
            data: Document to chunk
            **kwargs: Additional options

        Returns:
            List of chunks
        """
        return await self.chunk(data, **kwargs)

    def _create_chunk(
        self,
        content: str,
        chunk_type: str = "text",
        metadata: dict = None,
        index: int = 0
    ) -> Chunk:
        """
        Create a chunk with standard metadata.

        Args:
            content: Chunk content
            chunk_type: Type of chunk
            metadata: Additional metadata
            index: Chunk index

        Returns:
            Chunk object
        """
        meta = metadata or {}
        return Chunk(
            content=content,
            chunk_type=chunk_type,
            metadata=meta,
            index=index,
        )
