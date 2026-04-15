"""Unified RAG service entry point."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.rag.types import SearchResult
from services.rag.factory import get_pipeline, list_pipelines, has_pipeline
from services.rag.pipeline import DEFAULT_KB_BASE_DIR

logger = logging.getLogger("RAGService")


class RAGService:
    """Unified RAG service that orchestrates document processing and retrieval."""

    def __init__(
        self,
        kb_base_dir: Optional[str] = None,
        provider: Optional[str] = None,
    ):
        """
        Initialize RAG service.

        Args:
            kb_base_dir: Base directory for knowledge bases
            provider: Pipeline provider name (default: "default")
        """
        self.kb_base_dir = kb_base_dir or DEFAULT_KB_BASE_DIR
        self.provider = provider or "default"
        self._pipeline = None
        self.logger = logger

    def _get_pipeline(self):
        """Get or create pipeline instance."""
        if self._pipeline is None:
            self._pipeline = get_pipeline(
                self.provider,
                kb_base_dir=self.kb_base_dir,
            )
        return self._pipeline

    async def initialize_kb(
        self,
        kb_name: str,
        file_paths: List[str],
        progress_callback: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """
        Initialize a knowledge base from files.

        Args:
            kb_name: Knowledge base name
            file_paths: List of file paths to process
            progress_callback: Optional progress callback (stage, progress)
            **kwargs: Additional options

        Returns:
            True if successful
        """
        self.logger.info(f"Initializing KB '{kb_name}' with provider '{self.provider}'")

        pipeline = self._get_pipeline()
        if progress_callback:
            pipeline.on_progress(progress_callback)

        try:
            success = await pipeline.initialize(
                kb_name=kb_name,
                file_paths=file_paths,
                **kwargs
            )
            return success
        except Exception as e:
            self.logger.error(f"Failed to initialize KB: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    async def search(
        self,
        query: str,
        kb_name: str,
        top_k: int = 5,
        **kwargs
    ) -> SearchResult:
        """
        Search a knowledge base.

        Args:
            query: Search query
            kb_name: Knowledge base name
            top_k: Number of results to return
            **kwargs: Additional options

        Returns:
            SearchResult with matching chunks
        """
        self.logger.info(f"Searching KB '{kb_name}': {query[:50]}...")

        try:
            pipeline = self._get_pipeline()
            result = await pipeline.search(
                query=query,
                kb_name=kb_name,
                top_k=top_k,
                **kwargs
            )
            return result
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

            return SearchResult(
                query=query,
                content=f"Search failed: {str(e)}",
                chunks=[],
                sources=[],
                search_time_ms=0.0,
                metadata={"error": str(e)},
            )

    async def add_documents(
        self,
        kb_name: str,
        file_paths: List[str],
        **kwargs
    ) -> bool:
        """
        Add documents to an existing knowledge base.

        Args:
            kb_name: Knowledge base name
            file_paths: List of file paths to add
            **kwargs: Additional options

        Returns:
            True if successful
        """
        self.logger.info(f"Adding {len(file_paths)} documents to KB '{kb_name}'")

        try:
            pipeline = self._get_pipeline()
            success = await pipeline.add_documents(kb_name, file_paths, **kwargs)
            return success
        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            return False

    async def delete_kb(self, kb_name: str) -> bool:
        """
        Delete a knowledge base.

        Args:
            kb_name: Knowledge base name

        Returns:
            True if successful
        """
        self.logger.info(f"Deleting KB '{kb_name}'")

        try:
            pipeline = self._get_pipeline()
            success = await pipeline.delete(kb_name)
            return success
        except Exception as e:
            self.logger.error(f"Failed to delete KB: {e}")
            return False

    async def smart_retrieve(
        self,
        context: str,
        kb_name: str,
        query_hints: Optional[List[str]] = None,
        max_queries: int = 3,
        **kwargs
    ) -> SearchResult:
        """
        Smart retrieval with query expansion.

        Generates multiple queries from context and aggregates results.

        Args:
            context: Context to generate queries from
            kb_name: Knowledge base name
            query_hints: Optional pre-generated queries
            max_queries: Maximum number of queries to generate
            **kwargs: Additional options

        Returns:
            Aggregated SearchResult
        """
        import asyncio
        import time

        start_time = time.time()

        # Generate queries if not provided
        queries = query_hints if query_hints else await self._generate_queries(context, max_queries)
        self.logger.info(f"Smart retrieve with {len(queries)} queries: {queries}")

        # Execute all queries
        tasks = [self.search(q, kb_name, **kwargs) for q in queries]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        all_chunks = []
        all_sources = []
        seen_contents = set()

        for result in results:
            if isinstance(result, Exception):
                continue

            for chunk in result.chunks:
                # Deduplicate by content hash
                content_hash = hash(chunk.content[:100])
                if content_hash not in seen_contents:
                    seen_contents.add(content_hash)
                    all_chunks.append(chunk)

            all_sources.extend(result.sources)

        # Sort by score if available
        all_sources.sort(key=lambda x: x.score, reverse=True)

        # Aggregate content
        content = "\n\n".join([chunk.content for chunk in all_chunks[:kwargs.get("top_k", 5)]])

        search_time = (time.time() - start_time) * 1000

        return SearchResult(
            query=context[:100],
            content=content,
            chunks=all_chunks,
            sources=all_sources,
            search_time_ms=search_time,
            metadata={"queries": queries, "result_count": len(all_chunks)},
        )

    async def _generate_queries(self, context: str, n: int) -> List[str]:
        """
        Generate search queries from context.

        Args:
            context: Context text
            n: Number of queries to generate

        Returns:
            List of queries
        """
        # Simple fallback: use context and variations
        queries = [context[:200]]

        # Add variations
        if len(context) > 100:
            # Extract key sentences
            sentences = context.split("。")
            for sent in sentences[:n-1]:
                if len(sent.strip()) > 20:
                    queries.append(sent.strip()[:200])
                if len(queries) >= n:
                    break

        return queries[:n]

    def list_kbs(self) -> List[Dict[str, Any]]:
        """
        List all knowledge bases.

        Returns:
            List of KB info dictionaries
        """
        kb_dir = Path(self.kb_base_dir)
        if not kb_dir.exists():
            return []

        kbs = []
        for item in kb_dir.iterdir():
            if item.is_dir():
                metadata_path = item / "metadata.json"
                if metadata_path.exists():
                    try:
                        import json
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        kbs.append(metadata)
                    except Exception as e:
                        self.logger.warning(f"Failed to read metadata for {item.name}: {e}")
                else:
                    kbs.append({
                        "kb_name": item.name,
                        "document_count": 0,
                    })

        return kbs

    def get_kb_info(self, kb_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a knowledge base.

        Args:
            kb_name: Knowledge base name

        Returns:
            KB info dictionary or None
        """
        metadata_path = Path(self.kb_base_dir) / kb_name / "metadata.json"
        if metadata_path.exists():
            try:
                import json
                with open(metadata_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to read metadata: {e}")
        return None

    @staticmethod
    def list_providers() -> List[Dict[str, str]]:
        """List available pipeline providers."""
        return list_pipelines()

    @staticmethod
    def has_provider(name: str) -> bool:
        """Check if a provider exists."""
        return has_pipeline(name)
