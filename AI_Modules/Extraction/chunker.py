"""
Eduvance AI - Deterministic Token-Aware Chunking Engine
WBS 3.2 - Step 3: Chunking Engine

Segments extracted pages into atomic, source-anchored text chunks conforming to
Contract 1 (ExtractedChunk). Preserves originating document_id, page_number,
sequential chunk_index, and section hierarchy for RAG retrieval and citation grounding.

Owner: Member 2 (Content and RAG Engineer)
"""

import re
from typing import List, Optional
from uuid import UUID

from .schemas import ExtractedChunk, ExtractedPage

# Default chunking parameters
DEFAULT_CHUNK_SIZE_TOKENS = 400
DEFAULT_CHUNK_OVERLAP_TOKENS = 50
MIN_CHUNK_CHARACTERS = 50


class DocumentChunker:
    """Segments pages into overlapping, token-bounded chunks with page anchors."""

    def __init__(
        self,
        chunk_size_tokens: int = DEFAULT_CHUNK_SIZE_TOKENS,
        chunk_overlap_tokens: int = DEFAULT_CHUNK_OVERLAP_TOKENS,
        min_chunk_chars: int = MIN_CHUNK_CHARACTERS,
    ):
        if chunk_overlap_tokens >= chunk_size_tokens:
            raise ValueError("Overlap tokens must be strictly less than chunk size tokens.")

        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.min_chunk_chars = min_chunk_chars

    def chunk_pages(
        self,
        pages: List[ExtractedPage],
        document_id: UUID,
    ) -> List[ExtractedChunk]:
        """
        Processes a list of extracted pages into a sequence of source-anchored ExtractedChunk items.
        """
        if not pages:
            return []

        # 1. Deconstruct pages into atomic paragraph blocks tagged with page and section header
        blocks = self._extract_semantic_blocks(pages)
        if not blocks:
            return []

        # 2. Window through blocks accumulating token budgets
        chunks: List[ExtractedChunk] = []
        chunk_index = 0
        block_idx = 0
        total_blocks = len(blocks)

        while block_idx < total_blocks:
            current_tokens = 0
            window_blocks = []
            anchor_page = blocks[block_idx]["page_number"]
            current_header = blocks[block_idx]["section_header"]

            start_idx = block_idx

            while block_idx < total_blocks:
                b = blocks[block_idx]
                # If adding this block exceeds target chunk size and we already have content, break
                if current_tokens + b["tokens"] > self.chunk_size_tokens and window_blocks:
                    break

                window_blocks.append(b)
                current_tokens += b["tokens"]
                # Update header if a newer heading was encountered in this window
                if b["section_header"]:
                    current_header = b["section_header"]

                block_idx += 1

            # Construct chunk text
            chunk_text = "\n\n".join(b["text"] for b in window_blocks).strip()

            if len(chunk_text) >= self.min_chunk_chars:
                chunks.append(
                    ExtractedChunk(
                        document_id=document_id,
                        chunk_index=chunk_index,
                        page_number=anchor_page,
                        text_content=chunk_text,
                        token_count=current_tokens,
                        section_header=current_header,
                    )
                )
                chunk_index += 1

            # If we reached the end, stop
            if block_idx >= total_blocks:
                break

            # Calculate rewind step for overlap
            overlap_accum = 0
            rewind_steps = 0
            # Look backwards from block_idx to preserve overlap tokens
            for rev_idx in range(block_idx - 1, start_idx, -1):
                overlap_accum += blocks[rev_idx]["tokens"]
                if overlap_accum <= self.chunk_overlap_tokens:
                    rewind_steps += 1
                else:
                    break

            # Advance forward by at least 1 block to guarantee progress
            next_start = block_idx - rewind_steps
            if next_start <= start_idx:
                block_idx = start_idx + 1
            else:
                block_idx = next_start

        return chunks

    def _extract_semantic_blocks(self, pages: List[ExtractedPage]) -> List[dict]:
        """Splits pages into semantic paragraph blocks, detecting section headings."""
        blocks = []
        active_header: Optional[str] = None

        for page in pages:
            paragraphs = [p.strip() for p in page.text.split("\n\n") if p.strip()]

            for para in paragraphs:
                detected_header = self._detect_section_header(para)
                if detected_header:
                    active_header = detected_header
                    # If paragraph is merely a heading title, register it
                    if para == detected_header:
                        continue

                tokens = self.estimate_tokens(para)
                blocks.append(
                    {
                        "text": para,
                        "tokens": tokens,
                        "page_number": page.page_number,
                        "section_header": active_header,
                    }
                )

        return blocks

    @staticmethod
    def _detect_section_header(paragraph: str) -> Optional[str]:
        """Identifies numbered sections, Markdown headings, or all-caps short titles."""
        lines = paragraph.split("\n")
        first_line = lines[0].strip()

        # Markdown heading format (e.g. '## Section Name')
        if first_line.startswith("#"):
            return re.sub(r"^#+\s*", "", first_line).strip()

        # Numbered headings (e.g. '1.1 Overview', 'Section 2. Risk Management')
        numbered_pattern = r"^(?:Section\s+\d+|[0-9]+(?:\.[0-9]+)*)\s+[A-Za-z0-9].*$"
        if re.match(numbered_pattern, first_line) and len(first_line) < 100:
            return first_line

        # Short uppercase heading (e.g. 'EXECUTIVE SUMMARY')
        if first_line.isupper() and 3 < len(first_line) < 60:
            return first_line

        return None

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Deterministic token count estimation.
        Uses a standard ratio of ~1.33 tokens per whitespace-separated word,
        ensuring bounded chunk sizes without heavyweight tokenizer models.
        """
        if not text:
            return 0
        words = len(text.split())
        return max(1, int(words * 1.33))
