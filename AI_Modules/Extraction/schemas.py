"""
Eduvance AI - Content Extraction & Ingestion Schemas
WBS 3.2 - Step 1: Data Contracts

Defines Pydantic v2 validation models strictly adhering to:
- Contract 1 (Content Agent) from WBS 2.1 (Architecture & Contracts)
- Database entity representations (Database/models/all_models.py)

Owner: Member 2 (Content and RAG Engineer)
"""

from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DifficultyLevel(str, Enum):
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"


class DocumentValidationResult(BaseModel):
    """Result of validating an ingested document before extraction."""
    is_valid: bool = Field(description="Whether the document is acceptable for extraction")
    page_count: int = Field(ge=0, description="Total number of pages in the PDF")
    total_characters: int = Field(ge=0, default=0, description="Total extracted textual characters")
    total_words: int = Field(ge=0, default=0, description="Estimated total word count")
    average_chars_per_page: float = Field(ge=0.0, default=0.0, description="Average character density per page")
    is_scanned_or_empty: bool = Field(default=False, description="Flagged true if document appears to be scanned images or empty")
    error_message: Optional[str] = Field(default=None, description="Detailed validation error message if invalid")


class ExtractedPage(BaseModel):
    """Cleaned extracted page text with spatial page anchoring."""
    model_config = ConfigDict(from_attributes=True)

    page_number: int = Field(ge=1, description="Originating 1-indexed PDF page number")
    text: str = Field(description="Cleaned, normalized text content of the page")
    char_count: int = Field(ge=0, description="Total character count on the page")
    word_count: int = Field(ge=0, description="Total word count on the page")



class ExtractedChunk(BaseModel):
    """
    Atomic text chunk extracted from a source document.
    Directly conforms to WBS 2.1 Contract 1 (ContentExtractionOutput.chunks).
    """
    model_config = ConfigDict(from_attributes=True)

    chunk_id: UUID = Field(default_factory=uuid4, description="Unique chunk identifier")
    document_id: UUID = Field(description="Parent document identifier")
    chunk_index: int = Field(ge=0, description="Sequential 0-indexed position within the document")
    page_number: int = Field(ge=1, description="Originating 1-indexed PDF page anchor")
    text_content: str = Field(min_length=50, description="Cleaned textual content (minimum 50 chars)")
    token_count: int = Field(ge=1, description="Estimated or exact token count")
    section_header: Optional[str] = Field(default=None, description="Detected section heading for contextual grounding")


class ExtractedConcept(BaseModel):
    """
    Domain concept identified and structured from document chunks.
    Directly conforms to WBS 2.1 Contract 1 (ContentExtractionOutput.concepts).
    """
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID = Field(default_factory=uuid4, description="Unique concept identifier")
    name: str = Field(min_length=2, description="Concise concept title/term")
    description: str = Field(min_length=10, description="Clear explanatory summary of the concept")
    difficulty: DifficultyLevel = Field(default=DifficultyLevel.BEGINNER, description="Pedagogical complexity level")
    prerequisite_names: List[str] = Field(default_factory=list, description="Names of prerequisite concepts required to understand this concept")
    source_chunk_ids: List[UUID] = Field(default_factory=list, description="UUID references to source chunks providing evidence for this concept")


class ContentExtractionOutput(BaseModel):
    """
    Root contract output produced by the Content Agent.
    Strictly conforms to WBS 2.1 Contract 1 schema specification.
    """
    model_config = ConfigDict(from_attributes=True)

    course_id: UUID = Field(description="Associated course identifier")
    chunks: List[ExtractedChunk] = Field(min_length=1, description="List of source-anchored content chunks")
    concepts: List[ExtractedConcept] = Field(min_length=1, description="List of structured domain concepts")
