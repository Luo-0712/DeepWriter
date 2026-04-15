"""
Base Embedder
=============

Base class for embedding models.
"""

from abc import abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Callable

from services.rag.components.base import BaseComponent
from services.rag.types import Chunk


@dataclass
class EmbeddingConfig:
    """Configuration for embedding models."""
    model: str
    dim: int
    base_url: str
    api_key: str
    provider: str = "openai"  # openai, qwen, etc.


class BaseEmbedder(BaseComponent):
    """
    Base class for embedding models.

    All embedders must implement:
    - embed(texts, **kwargs) -> List[List[float]]
    - embed_query(text, **kwargs) -> List[float]
    """

    name: str = "base_embedder"

    def __init__(self, config: Optional[EmbeddingConfig] = None):
        super().__init__()
        self.config = config
        self._progress_callback: Optional[Callable[[int, int], None]] = None

    def set_progress_callback(self, callback: Optional[Callable[[int, int], None]]) -> None:
        """Set progress callback fn(batch_num, total_batches)."""
        self._progress_callback = callback

    @abstractmethod
    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Embed a list of texts.

        Args:
            texts: List of texts to embed
            **kwargs: Additional options

        Returns:
            List of embedding vectors
        """
        raise NotImplementedError("Subclasses must implement embed()")

    @abstractmethod
    async def embed_query(self, text: str, **kwargs) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Query text
            **kwargs: Additional options

        Returns:
            Embedding vector
        """
        raise NotImplementedError("Subclasses must implement embed_query()")

    async def embed_chunks(self, chunks: List[Chunk], **kwargs) -> List[Chunk]:
        """
        Embed a list of chunks and update them with embeddings.

        Args:
            chunks: List of chunks to embed
            **kwargs: Additional options

        Returns:
            Chunks with embeddings set
        """
        texts = [chunk.content for chunk in chunks]
        embeddings = await self.embed(texts, **kwargs)

        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        return chunks

    async def process(self, data: List[str], **kwargs) -> List[List[float]]:
        """
        Process interface (wrapper for embed).

        Args:
            data: List of texts to embed
            **kwargs: Additional options

        Returns:
            List of embeddings
        """
        return await self.embed(data, **kwargs)
