"""
Numbered Item Chunker
=====================

Chunker for numbered items (lists, steps, etc.) that keeps items together.
"""

import re
from typing import List, Tuple

from services.rag.components.chunkers.base import BaseChunker
from services.rag.types import Document, Chunk


class NumberedItemChunker(BaseChunker):
    """
    Chunker for numbered items.

    Preserves the integrity of numbered lists and step-by-step instructions.
    Useful for procedural documents, numbered lists, etc.
    """

    name: str = "numbered_item_chunker"

    def __init__(self, max_items_per_chunk: int = 10, max_chunk_size: int = 1500):
        super().__init__()
        self.max_items_per_chunk = max_items_per_chunk
        self.max_chunk_size = max_chunk_size

        # Pattern for numbered items (1., 1), (1), etc.)
        self.numbered_pattern = re.compile(
            r'^\s*(?:\d+[\.\)\]]\s+|\(\d+\)\s+)',
            re.MULTILINE
        )

    async def chunk(self, document: Document, **kwargs) -> List[Chunk]:
        """
        Split document by numbered items.

        Args:
            document: Document to chunk
            **kwargs: Additional options
                - max_items_per_chunk: Override default max items
                - max_chunk_size: Override default max size

        Returns:
            List of chunks
        """
        max_items = kwargs.get("max_items_per_chunk", self.max_items_per_chunk)
        max_size = kwargs.get("max_chunk_size", self.max_chunk_size)

        content = document.content

        # Extract numbered items
        items = self._extract_numbered_items(content)

        if not items:
            # No numbered items found, return single chunk
            return [self._create_chunk(
                content=content,
                chunk_type="text",
                metadata=document.metadata,
                index=0,
            )]

        chunks = []
        current_items = []
        current_count = 0
        current_size = 0
        index = 0

        for item_num, item_text in items:
            item_size = len(item_text)

            # Check if we need to start a new chunk
            if (current_count >= max_items or
                current_size + item_size > max_size) and current_items:
                chunk_text = "\n".join(current_items)
                chunk = self._create_chunk(
                    content=chunk_text,
                    chunk_type="list",
                    metadata={
                        "item_count": current_count,
                        "char_count": len(chunk_text),
                        "start_number": int(re.match(r'\d+', current_items[0]).group()),
                        **document.metadata,
                    },
                    index=index,
                )
                chunks.append(chunk)
                index += 1

                current_items = []
                current_count = 0
                current_size = 0

            current_items.append(item_text)
            current_count += 1
            current_size += item_size

        # Don't forget the last chunk
        if current_items:
            chunk_text = "\n".join(current_items)
            chunk = self._create_chunk(
                content=chunk_text,
                chunk_type="list",
                metadata={
                    "item_count": current_count,
                    "char_count": len(chunk_text),
                    "start_number": int(re.match(r'\d+', current_items[0]).group()),
                    **document.metadata,
                },
                index=index,
            )
            chunks.append(chunk)

        self.logger.info(f"Created {len(chunks)} numbered item chunks from {document.file_name}")
        return chunks

    def _extract_numbered_items(self, content: str) -> List[Tuple[int, str]]:
        """
        Extract numbered items from content.

        Args:
            content: Text content

        Returns:
            List of (item_number, item_text) tuples
        """
        items = []

        # Split by numbered pattern
        lines = content.splitlines()
        current_item = None
        current_text = []

        for line in lines:
            match = self.numbered_pattern.match(line)

            if match:
                # Save previous item
                if current_item is not None and current_text:
                    items.append((current_item, "\n".join(current_text).strip()))

                # Start new item
                num_match = re.search(r'\d+', line)
                current_item = int(num_match.group()) if num_match else 0
                current_text = [line]
            elif current_item is not None:
                # Continue current item (indented continuation)
                current_text.append(line)

        # Save last item
        if current_item is not None and current_text:
            items.append((current_item, "\n".join(current_text).strip()))

        return items
