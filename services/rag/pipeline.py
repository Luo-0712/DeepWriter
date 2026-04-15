"""
RAG Pipeline
============

Composable RAG pipeline with fluent API.
"""

import asyncio
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from services.rag.types import Document, SearchResult
from services.rag.components.base import BaseComponent
from services.rag.components.routing import FileTypeRouter
from services.rag.components.parsers.base import BaseParser
from services.rag.components.parsers.pdf import PDFParser
from services.rag.components.parsers.text import TextParser
from services.rag.components.chunkers.base import BaseChunker
from services.rag.components.chunkers.fixed import FixedSizeChunker
from services.rag.components.embedders.base import BaseEmbedder
from services.rag.components.indexers.base import BaseIndexer
from services.rag.components.retrievers.base import BaseRetriever


# Default knowledge base directory
DEFAULT_KB_BASE_DIR = str(
    Path(__file__).resolve().parent.parent.parent / "data" / "knowledge_bases"
)


class RAGPipeline:
    """
    Composable RAG pipeline.

    Build custom RAG pipelines using a fluent API:

        pipeline = (
            RAGPipeline("custom", kb_base_dir="/path/to/kb")
            .parser(PDFParser())
            .chunker(FixedSizeChunker(chunk_size=512))
            .embedder(OpenAIEmbedder())
            .indexer(VectorIndexer())
            .retriever(DenseRetriever())
        )

        await pipeline.initialize("kb_name", ["doc1.pdf"])
        result = await pipeline.search("query", "kb_name")
    """

    def __init__(self, name: str = "default", kb_base_dir: Optional[str] = None):
        """
        Initialize RAG pipeline.

        Args:
            name: Pipeline name for logging
            kb_base_dir: Base directory for knowledge bases
        """
        import logging
        self.name = name
        self.kb_base_dir = kb_base_dir or DEFAULT_KB_BASE_DIR
        self.logger = logging.getLogger(f"RAGPipeline:{name}")

        # Components
        self._parser: Optional[BaseParser] = None
        self._chunkers: List[BaseChunker] = []
        self._embedder: Optional[BaseEmbedder] = None
        self._indexer: Optional[BaseIndexer] = None
        self._retriever: Optional[BaseRetriever] = None

        # Progress callback
        self._progress_callback: Optional[Callable[[str, float], None]] = None

    # Fluent API methods
    def parser(self, p: BaseParser) -> "RAGPipeline":
        """Set the document parser."""
        self._parser = p
        return self

    def chunker(self, c: BaseChunker) -> "RAGPipeline":
        """Add a chunker to the pipeline."""
        self._chunkers.append(c)
        return self

    def embedder(self, e: BaseEmbedder) -> "RAGPipeline":
        """Set the embedder."""
        self._embedder = e
        return self

    def indexer(self, i: BaseIndexer) -> "RAGPipeline":
        """Set the indexer."""
        self._indexer = i
        return self

    def retriever(self, r: BaseRetriever) -> "RAGPipeline":
        """Set the retriever."""
        self._retriever = r
        return self

    def on_progress(self, callback: Optional[Callable[[str, float], None]]) -> "RAGPipeline":
        """Set progress callback (stage, progress)."""
        self._progress_callback = callback
        return self

    def _report_progress(self, stage: str, progress: float) -> None:
        """Report progress."""
        if self._progress_callback:
            try:
                self._progress_callback(stage, progress)
            except Exception as e:
                self.logger.warning(f"Progress callback error: {e}")

    async def initialize(self, kb_name: str, file_paths: List[str], **kwargs) -> bool:
        """
        Run full initialization pipeline.

        Uses FileTypeRouter to classify files and route them appropriately:
        - PDF/complex files -> configured parser
        - Text files -> direct text reading

        Args:
            kb_name: Knowledge base name
            file_paths: List of file paths to process
            **kwargs: Additional arguments passed to components

        Returns:
            True if successful
        """
        self.logger.info(f"Initializing KB '{kb_name}' with {len(file_paths)} files")
        self._report_progress("start", 0.0)

        if not self._parser:
            raise ValueError("No parser configured. Use .parser() to set one")
        if not self._embedder:
            raise ValueError("No embedder configured. Use .embedder() to set one")
        if not self._indexer:
            raise ValueError("No indexer configured. Use .indexer() to set one")

        # Stage 1: Parse documents with file type routing
        self.logger.info("Stage 1: Parsing documents...")
        self._report_progress("parsing", 0.1)

        classification = FileTypeRouter.classify_files(file_paths)
        self.logger.info(
            f"File classification: {len(classification.parser_files)} parser, "
            f"{len(classification.text_files)} text, "
            f"{len(classification.unsupported)} unsupported"
        )

        documents = []
        total_files = len(classification.parser_files) + len(classification.text_files)
        processed = 0

        # Process complex files (PDF, etc.) with configured parser
        for path in classification.parser_files:
            self.logger.info(f"Parsing (parser): {Path(path).name}")
            try:
                doc = await self._parser.parse(path, **kwargs)
                documents.append(doc)
            except Exception as e:
                self.logger.error(f"Failed to parse {path}: {e}")
            processed += 1
            self._report_progress("parsing", 0.1 + 0.2 * (processed / total_files))

        # Process text files directly
        text_parser = TextParser()
        for path in classification.text_files:
            self.logger.info(f"Parsing (direct text): {Path(path).name}")
            try:
                doc = await text_parser.parse(path, **kwargs)
                documents.append(doc)
            except Exception as e:
                self.logger.error(f"Failed to parse {path}: {e}")
            processed += 1
            self._report_progress("parsing", 0.1 + 0.2 * (processed / total_files))

        # Log unsupported files
        for path in classification.unsupported:
            self.logger.warning(f"Skipped unsupported file: {Path(path).name}")

        if not documents:
            self.logger.error("No valid documents found")
            return False

        self._report_progress("parsing", 0.3)

        # Stage 2: Chunk
        if self._chunkers:
            self.logger.info("Stage 2: Chunking...")
            self._report_progress("chunking", 0.4)

            for chunker in self._chunkers:
                for doc in documents:
                    try:
                        chunks = await chunker.chunk(doc, **kwargs)
                        doc.chunks.extend(chunks)
                    except Exception as e:
                        self.logger.error(f"Failed to chunk {doc.file_name}: {e}")

            total_chunks = sum(len(d.chunks) for d in documents)
            self.logger.info(f"Created {total_chunks} total chunks")
            self._report_progress("chunking", 0.5)
        else:
            # No chunker: treat entire document as one chunk
            for doc in documents:
                from services.rag.types import Chunk
                doc.chunks.append(Chunk(
                    content=doc.content,
                    chunk_type="text",
                    metadata=doc.metadata,
                ))
            self._report_progress("chunking", 0.5)

        # Stage 3: Embed
        self.logger.info("Stage 3: Embedding...")
        self._report_progress("embedding", 0.6)

        total_chunks = sum(len(d.chunks) for d in documents)
        embedded = 0

        # Set up progress callback for embedder
        def embedding_progress(batch_num, total_batches):
            progress = 0.6 + 0.2 * (batch_num / total_batches)
            self._report_progress("embedding", progress)

        self._embedder.set_progress_callback(embedding_progress)

        try:
            for doc in documents:
                if doc.chunks:
                    try:
                        await self._embedder.embed_chunks(doc.chunks, **kwargs)
                        embedded += len(doc.chunks)
                    except Exception as e:
                        self.logger.error(f"Failed to embed {doc.file_name}: {e}")
        finally:
            self._embedder.set_progress_callback(None)

        self.logger.info(f"Embedded {embedded}/{total_chunks} chunks")
        self._report_progress("embedding", 0.8)

        # Stage 4: Index
        self.logger.info("Stage 4: Indexing...")
        self._report_progress("indexing", 0.9)

        try:
            success = await self._indexer.index(kb_name, documents, **kwargs)
            if not success:
                self.logger.error("Indexing failed")
                return False
        except Exception as e:
            self.logger.error(f"Failed to index: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

        self._report_progress("complete", 1.0)
        self.logger.info(f"KB '{kb_name}' initialized successfully")
        return True

    async def search(self, query: str, kb_name: str, **kwargs) -> SearchResult:
        """
        Search the knowledge base.

        Args:
            query: Search query
            kb_name: Knowledge base name
            **kwargs: Additional arguments passed to retriever

        Returns:
            Search results
        """
        if not self._retriever:
            raise ValueError("No retriever configured. Use .retriever() to set one")

        self.logger.info(f"Searching KB '{kb_name}': {query[:50]}...")
        return await self._retriever.retrieve(query, kb_name, **kwargs)

    async def add_documents(self, kb_name: str, file_paths: List[str], **kwargs) -> bool:
        """
        Add documents to an existing knowledge base.

        Args:
            kb_name: Knowledge base name
            file_paths: List of file paths to add
            **kwargs: Additional arguments

        Returns:
            True if successful
        """
        self.logger.info(f"Adding {len(file_paths)} documents to KB '{kb_name}'")

        if not self._parser or not self._embedder or not self._indexer:
            raise ValueError("Pipeline not fully configured")

        # Parse
        classification = FileTypeRouter.classify_files(file_paths)
        documents = []

        for path in classification.parser_files:
            try:
                doc = await self._parser.parse(path, **kwargs)
                documents.append(doc)
            except Exception as e:
                self.logger.error(f"Failed to parse {path}: {e}")

        text_parser = TextParser()
        for path in classification.text_files:
            try:
                doc = await text_parser.parse(path, **kwargs)
                documents.append(doc)
            except Exception as e:
                self.logger.error(f"Failed to parse {path}: {e}")

        if not documents:
            return False

        # Chunk
        if self._chunkers:
            for chunker in self._chunkers:
                for doc in documents:
                    chunks = await chunker.chunk(doc, **kwargs)
                    doc.chunks.extend(chunks)
        else:
            for doc in documents:
                from services.rag.types import Chunk
                doc.chunks.append(Chunk(
                    content=doc.content,
                    chunk_type="text",
                    metadata=doc.metadata,
                ))

        # Embed
        for doc in documents:
            if doc.chunks:
                await self._embedder.embed_chunks(doc.chunks, **kwargs)

        # Add to index
        return await self._indexer.add_documents(kb_name, documents, **kwargs)

    async def delete(self, kb_name: str) -> bool:
        """
        Delete a knowledge base.

        Args:
            kb_name: Knowledge base name

        Returns:
            True if successful
        """
        # Validate kb_name to prevent path traversal
        if not kb_name or kb_name in (".", "..") or "/" in kb_name or "\\" in kb_name:
            raise ValueError(f"Invalid knowledge base name: {kb_name}")

        self.logger.info(f"Deleting KB '{kb_name}'")

        # Delete via indexer
        if self._indexer:
            try:
                await self._indexer.delete(kb_name)
            except Exception as e:
                self.logger.warning(f"Indexer delete error: {e}")

        # Clean up directory
        kb_dir = Path(self.kb_base_dir) / kb_name
        kb_dir = kb_dir.resolve()
        base_dir = Path(self.kb_base_dir).resolve()

        if not kb_dir.is_relative_to(base_dir):
            raise ValueError(f"Knowledge base path outside allowed directory: {kb_name}")

        if kb_dir.exists():
            shutil.rmtree(kb_dir)
            self.logger.info(f"Deleted KB directory: {kb_dir}")
            return True

        self.logger.warning(f"KB directory not found: {kb_dir}")
        return False
