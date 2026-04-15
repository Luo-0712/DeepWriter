"""
Fixed Size Chunker
==================

Chunker that splits text into fixed-size chunks with overlap.
"""

from typing import List

from services.rag.components.chunkers.base import BaseChunker
from services.rag.types import Document, Chunk


class FixedSizeChunker(BaseChunker):
    """
    Chunker that splits text into fixed-size chunks.

    Uses a sliding window approach with configurable chunk size and overlap.
    """

    name: str = "fixed_size_chunker"

    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        super().__init__()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def chunk(self, document: Document, **kwargs) -> List[Chunk]:
        """
        Split document into fixed-size chunks.

        Args:
            document: Document to chunk
            **kwargs: Additional options
                - chunk_size: Override default chunk size
                - chunk_overlap: Override default overlap

        Returns:
            List of chunks
        """
        chunk_size = kwargs.get("chunk_size", self.chunk_size)
        chunk_overlap = kwargs.get("chunk_overlap", self.chunk_overlap)

        content = document.content
        chunks = []

        # Simple character-based chunking
        start = 0
        index = 0

        while start < len(content):
            # Calculate end position
            end = start + chunk_size

            # Adjust to not break words (optional)
            if end < len(content) and kwargs.get("respect_boundaries", True):
                # Try to find a sentence or word boundary
                look_ahead = min(end + 100, len(content))
                text_segment = content[end:look_ahead]

                # Look for sentence ending
                for punct in [".\n", ". ", "!", "?", "\n\n"]:
                    pos = text_segment.find(punct)
                    if pos != -1:
                        end += pos + len(punct)
                        break

            # Extract chunk
            chunk_text = content[start:end].strip()

            if chunk_text:
                chunk = self._create_chunk(
                    content=chunk_text,
                    chunk_type="text",
                    metadata={
                        "start_char": start,
                        "end_char": end,
                        "char_count": len(chunk_text),
                        **document.metadata,
                    },
                    index=index,
                )
                chunks.append(chunk)
                index += 1

            # Move window
            start = end - chunk_overlap

        self.logger.info(f"Created {len(chunks)} fixed-size chunks from {document.file_name}")
        return chunks
