"""
Dense Retriever
===============

Dense vector similarity retriever using ChromaDB.
"""

import time
from typing import List, Optional

from services.rag.components.retrievers.base import BaseRetriever
from services.rag.types import SearchResult, Chunk, Source
from services.rag.components.indexers.vector import VectorIndexer
from services.rag.components.embedders.openai import OpenAIEmbedder


class DenseRetriever(BaseRetriever):
    """
    Dense vector similarity retriever.

    Uses vector embeddings and cosine similarity for retrieval.
    """

    name: str = "dense_retriever"

    def __init__(
        self,
        kb_base_dir: Optional[str] = None,
        top_k: int = 5,
        embedder: Optional[OpenAIEmbedder] = None,
    ):
        super().__init__(kb_base_dir, top_k)
        self.embedder = embedder or OpenAIEmbedder()
        self._indexer: Optional[VectorIndexer] = None

    def _get_indexer(self) -> VectorIndexer:
        """Get or create vector indexer."""
        if self._indexer is None:
            self._indexer = VectorIndexer(self.kb_base_dir)
        return self._indexer

    async def retrieve(self, query: str, kb_name: str, **kwargs) -> SearchResult:
        """
        Retrieve documents using dense vector similarity.

        Args:
            query: Search query
            kb_name: Knowledge base name
            **kwargs: Additional options
                - top_k: Override default top_k
                - score_threshold: Minimum similarity score (0-1)

        Returns:
            SearchResult with matching chunks
        """
        start_time = time.time()
        top_k = kwargs.get("top_k", self.top_k)
        score_threshold = kwargs.get("score_threshold", 0.0)

        self.logger.info(f"Retrieving from KB '{kb_name}': {query[:50]}...")

        try:
            # Get query embedding
            query_embedding = await self.embedder.embed_query(query)

            # Get collection
            indexer = self._get_indexer()
            collection = indexer.get_collection(kb_name)

            # Query collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k * 2,  # Get more for filtering
                include=["documents", "metadatas", "distances"],
            )

            # Process results
            chunks = []
            sources = []

            if results["ids"] and results["ids"][0]:
                ids = results["ids"][0]
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
                distances = results["distances"][0]

                for i, (doc_id, doc, meta, distance) in enumerate(
                    zip(ids, documents, metadatas, distances)
                ):
                    # Convert distance to similarity score (Chroma uses cosine distance)
                    # Cosine distance = 1 - cosine similarity
                    score = 1.0 - distance

                    if score < score_threshold:
                        continue

                    chunk = Chunk(
                        content=doc,
                        chunk_type=meta.get("chunk_type", "text"),
                        metadata=meta,
                    )
                    chunks.append(chunk)

                    source = Source(
                        title=meta.get("file_name", "Unknown"),
                        content=doc[:200],
                        source=meta.get("file_path", ""),
                        chunk_id=doc_id,
                        score=score,
                        metadata=meta,
                    )
                    sources.append(source)

                    if len(chunks) >= top_k:
                        break

            # Aggregate content
            content = "\n\n".join([chunk.content for chunk in chunks])

            search_time = (time.time() - start_time) * 1000

            self.logger.info(
                f"Retrieved {len(chunks)} chunks from KB '{kb_name}' in {search_time:.1f}ms"
            )

            return SearchResult(
                query=query,
                content=content,
                chunks=chunks,
                sources=sources,
                search_time_ms=search_time,
            )

        except Exception as e:
            self.logger.error(f"Retrieval failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

            return SearchResult(
                query=query,
                content="",
                chunks=[],
                sources=[],
                search_time_ms=(time.time() - start_time) * 1000,
                metadata={"error": str(e)},
            )

    async def batch_retrieve(
        self,
        queries: List[str],
        kb_name: str,
        **kwargs
    ) -> List[SearchResult]:
        """
        Retrieve for multiple queries.

        Args:
            queries: List of queries
            kb_name: Knowledge base name
            **kwargs: Additional options

        Returns:
            List of SearchResults
        """
        import asyncio

        tasks = [self.retrieve(q, kb_name, **kwargs) for q in queries]
        return await asyncio.gather(*tasks)
