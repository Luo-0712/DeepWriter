"""
OpenAI Embedder
===============

Embedding model using OpenAI-compatible API.
Supports OpenAI, Qwen, and other OpenAI-compatible providers.
"""

import asyncio
from typing import List, Optional

import httpx

from services.rag.components.embedders.base import BaseEmbedder, EmbeddingConfig


class OpenAIEmbedder(BaseEmbedder):
    """
    OpenAI-compatible embedding model.

    Works with:
    - OpenAI (text-embedding-3-small, text-embedding-3-large)
    - Qwen (text-embedding-v1, text-embedding-v2, text-embedding-v3)
    - Any OpenAI-compatible embedding API
    """

    name: str = "openai_embedder"

    # Default configurations for different providers
    DEFAULT_CONFIGS = {
        "qwen": EmbeddingConfig(
            model="text-embedding-v3",
            dim=1024,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="",
            provider="qwen",
        ),
        "openai": EmbeddingConfig(
            model="text-embedding-3-small",
            dim=1536,
            base_url="https://api.openai.com/v1",
            api_key="",
            provider="openai",
        ),
    }

    def __init__(self, config: Optional[EmbeddingConfig] = None, provider: str = "qwen"):
        """
        Initialize embedder.

        Args:
            config: Custom embedding config, or None to use defaults
            provider: Provider name (qwen, openai) if config is None
        """
        if config is None:
            config = self.DEFAULT_CONFIGS.get(provider, self.DEFAULT_CONFIGS["qwen"]).copy()

            # Try to load API key from settings
            try:
                from config.settings import Settings
                settings = Settings()  # 每次都创建新实例，避免缓存问题

                if provider == "qwen":
                    config.api_key = settings.qwen_api_key or ""
                    config.base_url = settings.qwen_api_base
                elif provider == "openai":
                    config.api_key = settings.openai_api_key or ""
                    config.base_url = settings.openai_api_base or config.base_url
            except Exception:
                pass

        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=60.0,
            )
        return self._client

    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Embed a list of texts.

        Args:
            texts: List of texts to embed
            **kwargs: Additional options
                - batch_size: Number of texts per batch (default: 10 for qwen, 25 for openai)

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Qwen API has batch size limit of 10
        default_batch_size = 10 if self.config.provider == "qwen" else 25
        batch_size = kwargs.get("batch_size", default_batch_size)
        all_embeddings = []

        total_batches = (len(texts) + batch_size - 1) // batch_size

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = i // batch_size + 1

            # Report progress
            if self._progress_callback:
                self._progress_callback(batch_num, total_batches)

            self.logger.debug(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")

            embeddings = await self._embed_batch(batch)
            all_embeddings.extend(embeddings)

            # Small delay to avoid rate limiting
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return all_embeddings

    async def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a single batch of texts.

        Args:
            texts: Batch of texts

        Returns:
            List of embeddings
        """
        client = self._get_client()

        payload = {
            "model": self.config.model,
            "input": texts,
        }

        # Add dimensions parameter for text-embedding-3 models
        if "text-embedding-3" in self.config.model:
            payload["dimensions"] = self.config.dim

        try:
            response = await client.post("/embeddings", json=payload)
            response.raise_for_status()
            data = response.json()

            # Extract embeddings
            embeddings = [item["embedding"] for item in data["data"]]
            return embeddings

        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            self.logger.error(f"Embedding error: {e}")
            raise

    async def embed_query(self, text: str, **kwargs) -> List[float]:
        """
        Embed a single query text.

        Args:
            text: Query text
            **kwargs: Additional options

        Returns:
            Embedding vector
        """
        embeddings = await self.embed([text], batch_size=1)
        return embeddings[0]

    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
