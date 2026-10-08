"""
Unit tests for ConceptExtractor
WBS 3.2 - Step 4: Concept Extraction & Graph Linking
"""

from uuid import uuid4
import pytest

from AI_Modules.Extraction.schemas import DifficultyLevel, ExtractedChunk
from AI_Modules.Extraction.concept_extractor import ConceptExtractor


def test_concept_extractor_empty_chunks():
    extractor = ConceptExtractor()
    assert extractor.extract_concepts([]) == []


def test_concept_extractor_definitional_patterns():
    doc_id = uuid4()
    chunk1 = ExtractedChunk(
        document_id=doc_id,
        chunk_index=0,
        page_number=1,
        text_content=(
            "Asset Management is defined as the systematic identification, categorization, "
            "and inventory of organizational physical systems, software, and external data feeds."
        ),
        token_count=25,
        section_header="1.0 Core Functions",
    )
    chunk2 = ExtractedChunk(
        document_id=doc_id,
        chunk_index=1,
        page_number=2,
        text_content=(
            "Risk Assessment refers to the quantitative and qualitative evaluation of operational threats, "
            "vulnerabilities, and adverse likelihood across infrastructure components."
        ),
        token_count=26,
        section_header="2.0 Risk Analysis",
    )

    extractor = ConceptExtractor()
    concepts = extractor.extract_concepts([chunk1, chunk2])

    assert len(concepts) >= 2
    concept_names = [c.name for c in concepts]
    assert "Asset Management" in concept_names
    assert "Risk Assessment" in concept_names

    # Check descriptions
    for c in concepts:
        assert len(c.description) >= 10
        assert len(c.source_chunk_ids) > 0

    # Risk Assessment is later, so Asset Management should be a prerequisite
    risk_concept = next(c for c in concepts if c.name == "Risk Assessment")
    assert "Asset Management" in risk_concept.prerequisite_names


def test_concept_extractor_section_header_concept():
    doc_id = uuid4()
    chunk = ExtractedChunk(
        document_id=doc_id,
        chunk_index=0,
        page_number=1,
        text_content=(
            "Organizations must establish formal boundary access control policies. "
            "Network perimeters require continuous monitoring and zero-trust authentication."
        ),
        token_count=22,
        section_header="Access Control",
    )

    extractor = ConceptExtractor()
    concepts = extractor.extract_concepts([chunk])

    assert len(concepts) >= 1
    assert any(c.name == "Access Control" for c in concepts)
    ac_concept = next(c for c in concepts if c.name == "Access Control")
    assert chunk.chunk_id in ac_concept.source_chunk_ids


def test_concept_extractor_difficulty_grading():
    doc_id = uuid4()
    chunk_intro = ExtractedChunk(
        document_id=doc_id,
        chunk_index=0,
        page_number=1,
        text_content="Introduction to cybersecurity fundamentals and overview of basic security hygiene principles.",
        token_count=15,
        section_header="Basic Fundamentals",
    )
    chunk_adv = ExtractedChunk(
        document_id=doc_id,
        chunk_index=9,
        page_number=10,
        text_content="Continuous adaptive risk governance and regulatory audit compliance metrics for Tier 4 enterprises.",
        token_count=18,
        section_header="Adaptive Governance",
    )

    extractor = ConceptExtractor()
    concepts = extractor.extract_concepts([chunk_intro, chunk_adv])

    intro_concept = next((c for c in concepts if "Fundamental" in c.name or "Basic" in c.name), None)
    adv_concept = next((c for c in concepts if "Governance" in c.name or "Adaptive" in c.name), None)

    if intro_concept:
        assert intro_concept.difficulty == DifficultyLevel.BEGINNER
    if adv_concept:
        assert adv_concept.difficulty == DifficultyLevel.ADVANCED
