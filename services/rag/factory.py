"""RAG pipeline factory.

This module provides a factory for creating RAG pipelines with
caching support for performance.
"""

from typing import Callable, Dict, List, Optional
import logging

from services.rag.pipeline import RAGPipeline
from services.rag.components.parsers.pdf import PDFParser
from services.rag.components.chunkers.fixed import FixedSizeChunker
from services.rag.components.embedders.openai import OpenAIEmbedder
from services.rag.components.indexers.vector import VectorIndexer
from services.rag.components.retrievers.dense import DenseRetriever

logger = logging.getLogger("RAGFactory")

DEFAULT_PROVIDER = "default"

# Pipeline registry - populated lazily
_PIPELINES: Dict[str, Callable] = {}
_PIPELINES_INITIALIZED = False

# Cached pipeline instances keyed by (name, kb_base_dir)
_PIPELINE_CACHE: Dict[tuple[str, Optional[str]], RAGPipeline] = {}


def _init_pipelines() -> None:
    """Lazily initialize the built-in pipeline registry."""
    global _PIPELINES_INITIALIZED
    if _PIPELINES_INITIALIZED:
        return

    def _build_default_pipeline(kb_base_dir: Optional[str] = None, **kwargs) -> RAGPipeline:
        """Build the default RAG pipeline."""
        provider = kwargs.get("embedder_provider", "qwen")

        pipeline = (
            RAGPipeline("default", kb_base_dir=kb_base_dir)
            .parser(PDFParser())
            .chunker(FixedSizeChunker(
                chunk_size=kwargs.get("chunk_size", 512),
                chunk_overlap=kwargs.get("chunk_overlap", 50),
            ))
            .embedder(OpenAIEmbedder(provider=provider))
            .indexer(VectorIndexer(kb_base_dir=kb_base_dir))
            .retriever(DenseRetriever(
                kb_base_dir=kb_base_dir,
                top_k=kwargs.get("top_k", 5),
                embedder=OpenAIEmbedder(provider=provider),
            ))
        )
        return pipeline

    _PIPELINES.update({
        DEFAULT_PROVIDER: _build_default_pipeline,
    })
    _PIPELINES_INITIALIZED = True
    logger.debug("Pipeline registry initialized")


def get_pipeline(
    name: str = DEFAULT_PROVIDER,
    kb_base_dir: Optional[str] = None,
    use_cache: bool = True,
    **kwargs
) -> RAGPipeline:
    """Get a pipeline instance by name.

    Args:
        name: Pipeline name
        kb_base_dir: Base directory for knowledge bases
        use_cache: Whether to use cached instance
        **kwargs: Additional arguments passed to pipeline factory

    Returns:
        RAGPipeline instance

    Raises:
        ValueError: If pipeline name is unknown
    """
    _init_pipelines()

    normalized_name = name.strip().lower()
    if normalized_name not in _PIPELINES:
        available = sorted(_PIPELINES.keys())
        raise ValueError(f"Unknown pipeline: {name}. Available: {available}")

    # Check cache
    cache_key = (normalized_name, kb_base_dir)
    if use_cache and cache_key in _PIPELINE_CACHE:
        logger.debug(f"Returning cached pipeline: {name}")
        return _PIPELINE_CACHE[cache_key]

    # Create new instance
    factory = _PIPELINES[normalized_name]
    try:
        instance = factory(kb_base_dir=kb_base_dir, **kwargs)

        # Cache if no custom kwargs
        if use_cache and not kwargs:
            _PIPELINE_CACHE[cache_key] = instance
            logger.debug(f"Cached pipeline: {name}")

        return instance
    except Exception as e:
        logger.error(f"Failed to create pipeline '{name}': {e}")
        raise


def list_pipelines() -> List[Dict[str, str]]:
    """List available pipelines.

    Returns:
        List of pipeline info dictionaries
    """
    _init_pipelines()

    return [
        {
            "id": DEFAULT_PROVIDER,
            "name": "Default",
            "description": "Standard RAG pipeline with ChromaDB vector store.",
        }
    ]


def register_pipeline(name: str, factory: Callable[..., RAGPipeline]) -> None:
    """Register a custom pipeline factory.

    Args:
        name: Pipeline name
        factory: Factory function that returns RAGPipeline
    """
    _init_pipelines()
    normalized_name = name.strip().lower()
    _PIPELINES[normalized_name] = factory
    logger.info(f"Registered pipeline: {name}")

    # Clear cache for this pipeline type
    keys_to_remove = [k for k in _PIPELINE_CACHE if k[0] == normalized_name]
    for key in keys_to_remove:
        del _PIPELINE_CACHE[key]


def has_pipeline(name: str) -> bool:
    """Check whether a pipeline exists.

    Args:
        name: Pipeline name

    Returns:
        True if pipeline exists
    """
    _init_pipelines()
    candidate = (name or "").strip().lower()
    return candidate in _PIPELINES


def clear_cache() -> None:
    """Clear the pipeline cache."""
    global _PIPELINE_CACHE
    _PIPELINE_CACHE.clear()
    logger.debug("Pipeline cache cleared")


def create_custom_pipeline(
    kb_base_dir: Optional[str] = None,
    parser: Optional[str] = "pdf",
    chunker: Optional[str] = "fixed",
    embedder: str = "qwen",
    indexer: str = "vector",
    retriever: str = "dense",
    **kwargs
) -> RAGPipeline:
    """Create a custom pipeline with specified components.

    Args:
        kb_base_dir: Base directory for knowledge bases
        parser: Parser type (pdf, text, markdown)
        chunker: Chunker type (fixed, semantic, numbered)
        embedder: Embedder provider (qwen, openai)
        indexer: Indexer type (vector)
        retriever: Retriever type (dense)
        **kwargs: Additional configuration

    Returns:
        Configured RAGPipeline
    """
    from services.rag.components.parsers.text import TextParser
    from services.rag.components.parsers.markdown import MarkdownParser
    from services.rag.components.chunkers.semantic import SemanticChunker
    from services.rag.components.chunkers.numbered_item import NumberedItemChunker

    pipeline = RAGPipeline("custom", kb_base_dir=kb_base_dir)

    # Parser
    if parser == "pdf":
        pipeline.parser(PDFParser())
    elif parser == "markdown":
        pipeline.parser(MarkdownParser())
    elif parser == "text":
        pipeline.parser(TextParser())

    # Chunker
    if chunker == "fixed":
        pipeline.chunker(FixedSizeChunker(
            chunk_size=kwargs.get("chunk_size", 512),
            chunk_overlap=kwargs.get("chunk_overlap", 50),
        ))
    elif chunker == "semantic":
        pipeline.chunker(SemanticChunker(
            max_chunk_size=kwargs.get("max_chunk_size", 1000),
        ))
    elif chunker == "numbered":
        pipeline.chunker(NumberedItemChunker())

    # Embedder
    embedder_instance = OpenAIEmbedder(provider=embedder)
    pipeline.embedder(embedder_instance)

    # Indexer
    if indexer == "vector":
        pipeline.indexer(VectorIndexer(kb_base_dir=kb_base_dir))

    # Retriever
    if retriever == "dense":
        pipeline.retriever(DenseRetriever(
            kb_base_dir=kb_base_dir,
            top_k=kwargs.get("top_k", 5),
            embedder=embedder_instance,
        ))

    return pipeline
