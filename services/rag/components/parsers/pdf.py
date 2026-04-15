"""
PDF Parser
==========

Parser for PDF documents using PyMuPDF.
"""

from pathlib import Path
from typing import List, Tuple

from services.rag.components.parsers.base import BaseParser
from services.rag.types import Document


class PDFParser(BaseParser):
    """
    Parser for PDF documents.

    Uses PyMuPDF (fitz) for text extraction.
    Extracts text page by page with page numbers.
    """

    name: str = "pdf_parser"

    def __init__(self):
        super().__init__()
        self._fitz = None

    def _get_fitz(self):
        """Lazy import fitz to avoid dependency issues."""
        if self._fitz is None:
            try:
                import fitz
                self._fitz = fitz
            except ImportError:
                raise ImportError(
                    "PyMuPDF (fitz) is required for PDF parsing. "
                    "Install with: pip install pymupdf"
                )
        return self._fitz

    async def parse(self, file_path: str, **kwargs) -> Document:
        """
        Parse a PDF file.

        Args:
            file_path: Path to the PDF file
            **kwargs: Additional options
                - extract_pages: bool = True - Extract page-by-page text

        Returns:
            Parsed Document with page metadata
        """
        self.logger.info(f"Parsing PDF: {file_path}")

        fitz = self._get_fitz()
        extract_pages = kwargs.get("extract_pages", True)

        try:
            doc = fitz.open(file_path)
            texts = []
            pages_info = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()

                if text.strip():
                    texts.append(text)
                    pages_info.append({
                        "page_number": page_num + 1,
                        "char_count": len(text),
                    })

            doc.close()

            full_text = "\n\n".join(texts)

            # Extract metadata
            metadata = self._extract_metadata(file_path)
            metadata["parser"] = self.name
            metadata["page_count"] = len(pages_info)
            metadata["pages"] = pages_info

            document = Document(
                content=full_text,
                file_path=file_path,
                file_type="pdf",
                metadata=metadata,
            )

            self.logger.info(
                f"Parsed PDF: {len(full_text)} characters, "
                f"{len(pages_info)} pages"
            )
            return document

        except Exception as e:
            self.logger.error(f"Failed to parse PDF {file_path}: {e}")
            raise

    async def parse_with_pages(self, file_path: str, **kwargs) -> List[Tuple[int, str]]:
        """
        Parse PDF and return text by page.

        Args:
            file_path: Path to the PDF file
            **kwargs: Additional options

        Returns:
            List of (page_number, text) tuples
        """
        fitz = self._get_fitz()
        result = []

        try:
            doc = fitz.open(file_path)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    result.append((page_num + 1, text))

            doc.close()
            return result

        except Exception as e:
            self.logger.error(f"Failed to parse PDF pages {file_path}: {e}")
            raise
