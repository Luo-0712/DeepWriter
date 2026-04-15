"""
Semantic Chunker
================

Chunker that splits text by semantic boundaries (paragraphs, sections).
"""

import re
from typing import List

from services.rag.components.chunkers.base import BaseChunker
from services.rag.types import Document, Chunk


class SemanticChunker(BaseChunker):
    """
    Chunker that splits text by semantic boundaries.

    Uses paragraph breaks, section headers, and other semantic markers
    to create meaningful chunks.
    """

    name: str = "semantic_chunker"

    def __init__(self, max_chunk_size: int = 1000, min_chunk_size: int = 100):
        super().__init__()
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

        # Patterns for semantic boundaries
        self.paragraph_pattern = re.compile(r'\n\s*\n')
        self.heading_pattern = re.compile(r'^(#{1,6}\s+|\w+[:\-]\s*$)', re.MULTILINE)

    async def chunk(self, document: Document, **kwargs) -> List[Chunk]:
        """
        Split document into semantic chunks.

        Args:
            document: Document to chunk
            **kwargs: Additional options
                - max_chunk_size: Override default max size
                - min_chunk_size: Override default min size

        Returns:
            List of chunks
        """
        max_size = kwargs.get("max_chunk_size", self.max_chunk_size)
        min_size = kwargs.get("min_chunk_size", self.min_chunk_size)

        content = document.content
        chunks = []

        # First, try to split by paragraphs
        paragraphs = self._split_by_paragraphs(content)

        current_chunk = []
        current_size = 0
        index = 0

        for para in paragraphs:
            para_size = len(para)

            # If adding this paragraph exceeds max size, finalize current chunk
            if current_size + para_size > max_size and current_chunk:
                chunk_text = "\n\n".join(current_chunk).strip()
                if len(chunk_text) >= min_size:
                    chunk = self._create_chunk(
                        content=chunk_text,
                        chunk_type="text",
                        metadata={
                            "char_count": len(chunk_text),
                            **document.metadata,
                        },
                        index=index,
                    )
                    chunks.append(chunk)
                    index += 1

                # Start new chunk with overlap (last paragraph)
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_size = sum(len(p) for p in current_chunk)

            current_chunk.append(para)
            current_size += para_size

        # Don't forget the last chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk).strip()
            if len(chunk_text) >= min_size // 2:  # More lenient for last chunk
                chunk = self._create_chunk(
                    content=chunk_text,
                    chunk_type="text",
                    metadata={
                        "char_count": len(chunk_text),
                        **document.metadata,
                    },
                    index=index,
                )
                chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} semantic chunks from {document.file_name}")
        return chunks

    def _split_by_paragraphs(self, content: str) -> List[str]:
        """
        Split content into paragraphs.

        Args:
            content: Text content

        Returns:
            List of paragraphs
        """
        # Split by multiple newlines (paragraph breaks)
        paragraphs = self.paragraph_pattern.split(content)

        # Clean up and filter empty paragraphs
        cleaned = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 10:  # Filter out very short fragments
                cleaned.append(para)

        return cleaned

    def _detect_chunk_type(self, text: str) -> str:
        """
        Detect the type of content in a chunk.

        Args:
            text: Chunk text

        Returns:
            Type string
        """
        text = text.strip()

        # Check for code blocks
        if text.startswith("```") or text.startswith("    "):
            return "code"

        # Check for headings
        if self.heading_pattern.match(text):
            return "heading"

        # Check for lists
        if re.match(r'^[\s]*[-*+\d]\.', text):
            return "list"

        return "text"
