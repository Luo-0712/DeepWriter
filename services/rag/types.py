"""
RAG Types
=========

Data types for the RAG pipeline.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


class ChunkType(str, Enum):
    """Chunk type classification"""
    TEXT = "text"
    HEADING = "heading"
    CODE = "code"
    LIST = "list"
    TABLE = "table"
    QUOTE = "quote"
    DEFINITION = "definition"
    THEOREM = "theorem"
    EQUATION = "equation"
    FIGURE = "figure"


@dataclass
class Chunk:
    """
    Document chunk.

    Represents a portion of a document with optional metadata and embedding.
    """
    content: str
    chunk_type: str = "text"
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    index: int = 0

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return {
            "content": self.content,
            "chunk_type": self.chunk_type,
            "metadata": self.metadata,
            "index": self.index,
        }


@dataclass
class Document:
    """
    Parsed document.

    Contains the full document content, metadata, and chunks.
    """
    content: str
    file_path: str = ""
    file_name: str = ""
    file_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunks: List[Chunk] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.chunks is None:
            self.chunks = []
        # Auto-extract file_name from file_path if not provided
        if not self.file_name and self.file_path:
            import os
            self.file_name = os.path.basename(self.file_path)

    def add_chunk(self, chunk: Chunk) -> None:
        """Add a chunk to the document."""
        chunk.index = len(self.chunks)
        self.chunks.append(chunk)

    def get_chunks_by_type(self, chunk_type: str) -> List[Chunk]:
        """Get all chunks of a specific type."""
        return [c for c in self.chunks if c.chunk_type == chunk_type]

    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        return {
            "content": self.content[:1000] + "..." if len(self.content) > 1000 else self.content,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "metadata": self.metadata,
            "chunk_count": len(self.chunks),
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Source:
    """
    Source information for a retrieved chunk.
    """
    title: str = ""
    content: str = ""
    source: str = ""
    page: Optional[int] = None
    chunk_id: str = ""
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert source to dictionary."""
        return {
            "title": self.title,
            "content": self.content[:200] if len(self.content) > 200 else self.content,
            "source": self.source,
            "page": self.page,
            "chunk_id": self.chunk_id,
            "score": round(self.score, 4) if self.score else 0.0,
            "metadata": self.metadata,
        }


@dataclass
class SearchResult:
    """
    Search result from RAG query.
    """
    query: str
    content: str
    chunks: List[Chunk] = field(default_factory=list)
    sources: List[Source] = field(default_factory=list)
    total_chunks: int = 0
    search_time_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.chunks is None:
            self.chunks = []
        if self.sources is None:
            self.sources = []
        if self.metadata is None:
            self.metadata = {}
        self.total_chunks = len(self.chunks)

    def to_dict(self) -> Dict[str, Any]:
        """Convert search result to dictionary."""
        return {
            "query": self.query,
            "content": self.content,
            "sources": [s.to_dict() for s in self.sources],
            "total_chunks": self.total_chunks,
            "search_time_ms": round(self.search_time_ms, 2),
            "metadata": self.metadata,
        }


@dataclass
class FileClassification:
    """
    Result of file classification.

    Attributes:
        parser_files: Files requiring parser processing (PDF, DOCX, etc.)
        text_files: Files that can be read directly as text
        unsupported: Files with unsupported formats
    """
    parser_files: List[str] = field(default_factory=list)
    text_files: List[str] = field(default_factory=list)
    unsupported: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.parser_files is None:
            self.parser_files = []
        if self.text_files is None:
            self.text_files = []
        if self.unsupported is None:
            self.unsupported = []

    def total_files(self) -> int:
        """Get total number of files."""
        return len(self.parser_files) + len(self.text_files) + len(self.unsupported)
