"""
Text Parser
===========

Parser for plain text files.
"""

from services.rag.components.parsers.base import BaseParser
from services.rag.types import Document
from services.rag.components.routing import FileTypeRouter


class TextParser(BaseParser):
    """
    Parser for plain text files.

    Supports various text encodings with automatic detection.
    """

    name: str = "text_parser"

    async def parse(self, file_path: str, **kwargs) -> Document:
        """
        Parse a text file.

        Args:
            file_path: Path to the text file
            **kwargs: Additional options

        Returns:
            Parsed Document
        """
        self.logger.info(f"Parsing text file: {file_path}")

        # Read file with encoding detection
        content = await FileTypeRouter.read_text_file(file_path)

        # Extract metadata
        metadata = self._extract_metadata(file_path)
        metadata["parser"] = self.name

        # Create document
        document = Document(
            content=content,
            file_path=file_path,
            file_type="text",
            metadata=metadata,
        )

        self.logger.info(f"Parsed text file: {len(content)} characters")
        return document
