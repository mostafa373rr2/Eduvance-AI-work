"""
Eduvance AI - Page-by-Page Text Extraction Engine
WBS 3.2 - Step 2: Text Extractor

Extracts text from validated PDFs while preserving spatial page boundaries
and cleaning layout artifacts for downstream chunking and grounding.

Owner: Member 2 (Content and RAG Engineer)
"""

import io
import re
import unicodedata
from pathlib import Path
from typing import List, Union, BinaryIO
from pypdf import PdfReader

from .schemas import ExtractedPage
from .pdf_validator import PDFValidator


class TextExtractor:
    """Extracts and normalizes text page-by-page from digital PDF documents."""

    def __init__(self, validator: PDFValidator = None):
        self.validator = validator or PDFValidator()

    def extract_pages(self, source: Union[str, Path, bytes, BinaryIO]) -> List[ExtractedPage]:
        """
        Validates the PDF and extracts structured, cleaned pages with page anchors.
        Raises ValueError if validation fails.
        """
        # 1. Validation Gate
        val_result = self.validator.validate(source)
        if not val_result.is_valid:
            raise ValueError(f"PDF validation failed: {val_result.error_message}")

        # 2. Extract page by page
        stream = self._to_stream(source)
        reader = PdfReader(stream)
        extracted_pages: List[ExtractedPage] = []

        for idx, page in enumerate(reader.pages, start=1):
            raw_text = page.extract_text() or ""
            cleaned_text = self.clean_text(raw_text)

            extracted_pages.append(
                ExtractedPage(
                    page_number=idx,
                    text=cleaned_text,
                    char_count=len(cleaned_text),
                    word_count=len(cleaned_text.split()),
                )
            )

        return extracted_pages

    @staticmethod
    def clean_text(raw_text: str) -> str:
        """
        Normalizes extracted text:
        - Resolves Unicode abnormalities (NFKC)
        - Heuristically rejoins hyphenated line breaks (e.g. 'cyber-\nsecurity' -> 'cybersecurity')
        - Normalizes multiple spaces and extraneous newlines
        """
        if not raw_text:
            return ""

        # Normalize unicode characters
        text = unicodedata.normalize("NFKC", raw_text)

        # Replace Windows carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Reconnect hyphenated words split across lines
        text = re.sub(r"(\w+)-\n(\w+)", r"\1\2", text)

        # Collapse more than two consecutive newlines into two (preserving paragraph breaks)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Collapse excessive inline spaces and tabs into a single space
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]

        # Filter out empty lines while preserving paragraph separations
        cleaned_text = "\n".join(lines).strip()

        return cleaned_text

    @staticmethod
    def _to_stream(source: Union[str, Path, bytes, BinaryIO]) -> Union[io.BytesIO, BinaryIO]:
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.is_file():
                raise FileNotFoundError(f"Source file not found: {source}")
            return io.BytesIO(path.read_bytes())
        elif isinstance(source, bytes):
            return io.BytesIO(source)
        return source
