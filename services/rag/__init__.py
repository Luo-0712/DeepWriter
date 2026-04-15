"""
RAG Service
===========

Retrieval-Augmented Generation service for DeepWriter.
Provides document parsing, chunking, embedding, indexing and retrieval capabilities.
"""

from services.rag.types import Chunk, Document, SearchResult, Source, FileClassification
from services.rag.service import RAGService
from services.rag.factory import get_pipeline, register_pipeline, list_pipelines, create_custom_pipeline
from services.rag.pipeline import RAGPipeline

# Components
from services.rag.components.base import Component, BaseComponent
from services.rag.components.routing import FileTypeRouter

# Parsers
from services.rag.components.parsers.base import BaseParser
from services.rag.components.parsers.pdf import PDFParser
from services.rag.components.parsers.text import TextParser
from services.rag.components.parsers.markdown import MarkdownParser

# Chunkers
from services.rag.components.chunkers.base import BaseChunker
from services.rag.components.chunkers.fixed import FixedSizeChunker
from services.rag.components.chunkers.semantic import SemanticChunker
from services.rag.components.chunkers.numbered_item import NumberedItemChunker

# Embedders
from services.rag.components.embedders.base import BaseEmbedder, EmbeddingConfig
from services.rag.components.embedders.openai import OpenAIEmbedder

# Indexers
from services.rag.components.indexers.base import BaseIndexer
from services.rag.components.indexers.vector import VectorIndexer

# Retrievers
from services.rag.components.retrievers.base import BaseRetriever
from services.rag.components.retrievers.dense import DenseRetriever

__all__ = [
    # Types
    "Chunk",
    "Document",
    "SearchResult",
    "Source",
    "FileClassification",
    # Service
    "RAGService",
    "RAGPipeline",
    # Factory
    "get_pipeline",
    "register_pipeline",
    "list_pipelines",
    "create_custom_pipeline",
    # Components
    "Component",
    "BaseComponent",
    "FileTypeRouter",
    # Parsers
    "BaseParser",
    "PDFParser",
    "TextParser",
    "MarkdownParser",
    # Chunkers
    "BaseChunker",
    "FixedSizeChunker",
    "SemanticChunker",
    "NumberedItemChunker",
    # Embedders
    "BaseEmbedder",
    "EmbeddingConfig",
    "OpenAIEmbedder",
    # Indexers
    "BaseIndexer",
    "VectorIndexer",
    # Retrievers
    "BaseRetriever",
    "DenseRetriever",
]
