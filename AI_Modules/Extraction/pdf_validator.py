"""
Eduvance AI - PDF Ingestion & Validation Service
WBS 3.2 - Step 2: Document Validator

Enforces boundary constraints:
- Single PDF page count <= 50 pages
- Detects corrupt or password-protected files
- Rejects scanned / image-only PDFs with low character density (< 100 chars/page)

Owner: Member 2 (Content and RAG Engineer)
"""

import io
from pathlib import Path
from typing import Union, BinaryIO
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from .schemas import DocumentValidationResult

# Project-defined limits
MAX_PAGE_LIMIT = 50
MIN_AVG_CHARS_PER_PAGE = 100.0
MIN_TOTAL_CHARS = 150


class PDFValidator:
    """Validates PDF files according to Eduvance AI graduation project scope."""

    def __init__(
        self,
        max_pages: int = MAX_PAGE_LIMIT,
        min_avg_chars_per_page: float = MIN_AVG_CHARS_PER_PAGE,
        min_total_chars: int = MIN_TOTAL_CHARS,
    ):
        self.max_pages = max_pages
        self.min_avg_chars_per_page = min_avg_chars_per_page
        self.min_total_chars = min_total_chars

    def validate(self, source: Union[str, Path, bytes, BinaryIO]) -> DocumentValidationResult:
        """
        Validates a PDF from a filepath, byte stream, or binary buffer.
        """
        try:
            stream = self._to_stream(source)
            reader = PdfReader(stream)

            if reader.is_encrypted:
                return DocumentValidationResult(
                    is_valid=False,
                    page_count=0,
                    error_message="Encrypted/password-protected PDFs are not supported.",
                )

            page_count = len(reader.pages)
            if page_count == 0:
                return DocumentValidationResult(
                    is_valid=False,
                    page_count=0,
                    error_message="The uploaded PDF contains no pages.",
                )

            if page_count > self.max_pages:
                return DocumentValidationResult(
                    is_valid=False,
                    page_count=page_count,
                    error_message=f"Document exceeds maximum course page limit ({page_count} pages > {self.max_pages} pages allowed).",
                )

            # Sample/extract characters to compute textual density
            total_chars = 0
            total_words = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                cleaned = text.strip()
                total_chars += len(cleaned)
                total_words += len(cleaned.split())

            avg_chars = total_chars / page_count

            # Check if document appears to be scanned or image-only
            if avg_chars < self.min_avg_chars_per_page or total_chars < self.min_total_chars:
                return DocumentValidationResult(
                    is_valid=False,
                    page_count=page_count,
                    total_characters=total_chars,
                    total_words=total_words,
                    average_chars_per_page=round(avg_chars, 2),
                    is_scanned_or_empty=True,
                    error_message=(
                        f"Document contains insufficient extractable text (average {round(avg_chars, 1)} "
                        f"chars/page; minimum required: {self.min_avg_chars_per_page}). "
                        "Scanned images or OCR-dependent files are outside prototype scope."
                    ),
                )

            return DocumentValidationResult(
                is_valid=True,
                page_count=page_count,
                total_characters=total_chars,
                total_words=total_words,
                average_chars_per_page=round(avg_chars, 2),
                is_scanned_or_empty=False,
                error_message=None,
            )

        except (PdfReadError, Exception) as exc:
            return DocumentValidationResult(
                is_valid=False,
                page_count=0,
                error_message=f"Failed to parse PDF file: {str(exc)}",
            )

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
