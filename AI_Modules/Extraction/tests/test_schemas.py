"""
Unit tests for AI_Modules/Extraction schemas.
Verifies Contract 1 compliance and validation rules.
"""

from uuid import uuid4
import pytest
from pydantic import ValidationError

from AI_Modules.Extraction.schemas import (
    DifficultyLevel,
    DocumentValidationResult,
    ExtractedChunk,
    ExtractedConcept,
    ContentExtractionOutput,
)


def test_document_validation_result():
    res = DocumentValidationResult(
        is_valid=True,
        page_count=25,
        total_characters=15000,
        total_words=2500,
        average_chars_per_page=600.0,
        is_scanned_or_empty=False,
    )
    assert res.is_valid is True
    assert res.page_count == 25
    assert res.is_scanned_or_empty is False


def test_extracted_chunk_valid():
    doc_id = uuid4()
    chunk = ExtractedChunk(
        document_id=doc_id,
        chunk_index=0,
        page_number=1,
        text_content="This is a valid extracted textual content representing a paragraph from NIST guidelines with sufficient length.",
        token_count=20,
        section_header="1.1 Overview",
    )
    assert chunk.chunk_id is not None
    assert chunk.document_id == doc_id
    assert chunk.page_number == 1
    assert chunk.chunk_index == 0


def test_extracted_chunk_min_length_validation():
    with pytest.raises(ValidationError):
        ExtractedChunk(
            document_id=uuid4(),
            chunk_index=0,
            page_number=1,
            text_content="Too short",  # < 50 chars
            token_count=2,
        )


def test_extracted_concept_valid():
    concept = ExtractedConcept(
        name="Asset Management",
        description="Identifying and managing physical and software assets within an organization.",
        difficulty=DifficultyLevel.BEGINNER,
        prerequisite_names=["Basic Computing"],
        source_chunk_ids=[uuid4()],
    )
    assert concept.name == "Asset Management"
    assert concept.difficulty == DifficultyLevel.BEGINNER


def test_content_extraction_output_root():
    course_id = uuid4()
    doc_id = uuid4()
    chunk = ExtractedChunk(
        document_id=doc_id,
        chunk_index=0,
        page_number=1,
        text_content="This is a comprehensive overview of cybersecurity risk management principles for small businesses.",
        token_count=18,
    )
    concept = ExtractedConcept(
        name="Risk Assessment",
        description="The systematic process of identifying, analyzing, and evaluating organizational risks.",
        difficulty=DifficultyLevel.INTERMEDIATE,
        source_chunk_ids=[chunk.chunk_id],
    )
    output = ContentExtractionOutput(
        course_id=course_id,
        chunks=[chunk],
        concepts=[concept],
    )
    assert output.course_id == course_id
    assert len(output.chunks) == 1
    assert len(output.concepts) == 1
    assert output.concepts[0].source_chunk_ids[0] == chunk.chunk_id
