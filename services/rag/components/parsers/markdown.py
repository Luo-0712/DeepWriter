"""
Markdown Parser
===============

Parser for Markdown files with structure extraction.
"""

import re
from typing import List, Dict, Any

from services.rag.components.parsers.base import BaseParser
from services.rag.types import Document, Chunk, ChunkType
from services.rag.components.routing import FileTypeRouter


class MarkdownParser(BaseParser):
    """
    Parser for Markdown files.

    Extracts structure (headings, code blocks, lists) and creates chunks.
    """

    name: str = "markdown_parser"

    # Regex patterns for markdown elements
    HEADING_PATTERN = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK_PATTERN = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
    LIST_PATTERN = re.compile(r'^(\s*)[-*+]\s+(.+)$', re.MULTILINE)

    async def parse(self, file_path: str, **kwargs) -> Document:
        """
        Parse a Markdown file.

        Args:
            file_path: Path to the Markdown file
            **kwargs: Additional options
                - extract_structure: bool = True - Extract headings and structure

        Returns:
            Parsed Document with structure metadata
        """
        self.logger.info(f"Parsing Markdown: {file_path}")

        extract_structure = kwargs.get("extract_structure", True)

        # Read file
        content = await FileTypeRouter.read_text_file(file_path)

        # Extract metadata
        metadata = self._extract_metadata(file_path)
        metadata["parser"] = self.name

        # Extract structure if requested
        if extract_structure:
            structure = self._extract_structure(content)
            metadata["structure"] = structure

        document = Document(
            content=content,
            file_path=file_path,
            file_type="markdown",
            metadata=metadata,
        )

        self.logger.info(f"Parsed Markdown: {len(content)} characters")
        return document

    def _extract_structure(self, content: str) -> Dict[str, Any]:
        """
        Extract document structure from Markdown.

        Args:
            content: Markdown content

        Returns:
            Dictionary with structure information
        """
        structure = {
            "headings": [],
            "code_blocks": [],
            "list_items": [],
        }

        # Extract headings
        for match in self.HEADING_PATTERN.finditer(content):
            level = len(match.group(1))
            text = match.group(2).strip()
            structure["headings"].append({
                "level": level,
                "text": text,
            })

        # Extract code blocks
        for match in self.CODE_BLOCK_PATTERN.finditer(content):
            language = match.group(1) or "text"
            code = match.group(2)
            structure["code_blocks"].append({
                "language": language,
                "line_count": len(code.splitlines()),
            })

        # Extract list items
        for match in self.LIST_PATTERN.finditer(content):
            indent = len(match.group(1))
            text = match.group(2).strip()
            structure["list_items"].append({
                "indent": indent,
                "text": text[:100],  # Truncate for metadata
            })

        return structure

    def split_by_headings(self, content: str) -> List[Dict[str, Any]]:
        """
        Split Markdown content by headings.

        Args:
            content: Markdown content

        Returns:
            List of sections with heading and content
        """
        sections = []
        current_heading = "Introduction"
        current_content = []

        lines = content.splitlines()

        for line in lines:
            heading_match = self.HEADING_PATTERN.match(line)

            if heading_match:
                # Save previous section
                if current_content:
                    sections.append({
                        "heading": current_heading,
                        "content": "\n".join(current_content).strip(),
                        "level": 0 if current_heading == "Introduction" else 1,
                    })

                # Start new section
                level = len(heading_match.group(1))
                current_heading = heading_match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections.append({
                "heading": current_heading,
                "content": "\n".join(current_content).strip(),
                "level": 0 if current_heading == "Introduction" else 1,
            })

        return sections
