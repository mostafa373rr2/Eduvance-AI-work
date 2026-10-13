"""
Eduvance AI - Course Designer Engine Tests
WBS 3.3 - Course Curriculum & Syllabus Synthesis

Tests:
- Deterministic curriculum generation from Contract 1 extraction output.
- Pedagogical sequencing (prerequisites and beginner concepts ordered first).
- Bloom's taxonomy learning objectives formulation.
- Source chunk and target concept provenance guarantees.
- Bounded curriculum scaling (small vs large concept sets).
- LLM prompt generation and resilient JSON parsing fallback.

Owner: Member 2 (Content and RAG Engineer)
"""

from uuid import uuid4
import pytest

from AI_Modules.CourseDesign.course_designer import CourseDesigner
from AI_Modules.CourseDesign.schemas import CourseDesignOutput
from AI_Modules.Extraction.schemas import (
    ContentExtractionOutput,
    DifficultyLevel,
    ExtractedChunk,
    ExtractedConcept,
)


def test_generate_curriculum_produces_contract_2_valid_output(mock_extraction_output: ContentExtractionOutput):
    """Verifies that generated curriculum strictly satisfies all Contract 2 Pydantic constraints."""
    designer = CourseDesigner()
    result = designer.generate_curriculum(mock_extraction_output)

    assert isinstance(result, CourseDesignOutput)
    assert len(result.course_title) >= 5
    assert len(result.description) >= 20

    # Contract 2 bounds: 2 to 4 modules
    assert 2 <= len(result.modules) <= 4

    # Each module has 1 to 3 lessons
    for mod in result.modules:
        assert 1 <= len(mod.lessons) <= 3
        assert len(mod.title) >= 2
        assert len(mod.description) >= 5

        # Verify lesson sequence indices are sequential starting at 1
        for idx, lesson in enumerate(mod.lessons, start=1):
            assert lesson.lesson_sequence == idx
            assert 5 <= lesson.estimated_minutes <= 30
            assert len(lesson.learning_objectives) >= 2
            assert len(lesson.target_concept_ids) >= 1
            assert len(lesson.source_chunk_ids) >= 1


def test_pedagogical_concept_sequencing(mock_extraction_output: ContentExtractionOutput):
    """Verifies beginner and prerequisite concepts are scheduled in earlier modules."""
    designer = CourseDesigner()
    result = designer.generate_curriculum(mock_extraction_output)

    concept_lookup = {c.concept_id: c for c in mock_extraction_output.concepts}

    # Inspect Module 1 lessons
    mod1_concept_ids = []
    for lesson in result.modules[0].lessons:
        mod1_concept_ids.extend(lesson.target_concept_ids)

    mod1_concepts = [concept_lookup[cid] for cid in mod1_concept_ids]

    # First module must prioritize BEGINNER or zero-prerequisite concepts
    assert any(c.difficulty == DifficultyLevel.BEGINNER for c in mod1_concepts)
    assert any(len(c.prerequisite_names) == 0 for c in mod1_concepts)

    # Last module should host ADVANCED concepts
    last_mod_concept_ids = []
    for lesson in result.modules[-1].lessons:
        last_mod_concept_ids.extend(lesson.target_concept_ids)

    last_mod_concepts = [concept_lookup[cid] for cid in last_mod_concept_ids]
    assert any(c.difficulty == DifficultyLevel.ADVANCED for c in last_mod_concepts)


def test_learning_objectives_bloom_taxonomy(mock_extraction_output: ContentExtractionOutput):
    """Verifies that all learning objectives are phrased using Bloom's taxonomy action verbs."""
    designer = CourseDesigner()
    result = designer.generate_curriculum(mock_extraction_output)

    recognized_bloom_roots = {
        "identify", "define", "explain", "describe", "recognize", "summarize",
        "differentiate", "clarify", "apply", "implement", "analyze", "execute",
        "construct", "examine", "integrate", "demonstrate", "evaluate", "optimize",
        "formulate", "design", "assess", "synthesize", "standardize", "govern",
    }

    for mod in result.modules:
        for lesson in mod.lessons:
            assert len(lesson.learning_objectives) >= 2
            for obj in lesson.learning_objectives:
                first_word = obj.split()[0].lower()
                assert first_word in recognized_bloom_roots, (
                    f"Objective '{obj}' does not start with a recognized Bloom's taxonomy action verb."
                )


def test_citation_provenance_preservation(mock_extraction_output: ContentExtractionOutput):
    """Verifies that 100% of target concepts and source chunks in lessons link to original inputs."""
    designer = CourseDesigner()
    result = designer.generate_curriculum(mock_extraction_output)

    valid_concept_ids = {c.concept_id for c in mock_extraction_output.concepts}
    valid_chunk_ids = {c.chunk_id for c in mock_extraction_output.chunks}

    for mod in result.modules:
        for lesson in mod.lessons:
            for cid in lesson.target_concept_ids:
                assert cid in valid_concept_ids, f"Concept ID {cid} is not in source extraction concepts."
            for chid in lesson.source_chunk_ids:
                assert chid in valid_chunk_ids, f"Chunk ID {chid} is not in source extraction chunks."


def test_minimal_concepts_scaling():
    """Verifies curriculum generator handles small concept sets while honoring Contract 2 bounds [2, 4]."""
    course_id = uuid4()
    doc_id = uuid4()

    chunks = [
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            page_number=1,
            text_content="Basic computing principles include binary logic, registers, and execution cycles.",
            token_count=100,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=1,
            page_number=2,
            text_content="Memory hierarchy manages caching, RAM access, and long-term persistent storage.",
            token_count=110,
        ),
    ]

    concepts = [
        ExtractedConcept(
            concept_id=uuid4(),
            name="Binary Logic",
            description="Foundation of digital computing and electronic switching.",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisite_names=[],
            source_chunk_ids=[chunks[0].chunk_id],
        ),
        ExtractedConcept(
            concept_id=uuid4(),
            name="Memory Hierarchy",
            description="Structured architecture from CPU caches to persistent storage.",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisite_names=["Binary Logic"],
            source_chunk_ids=[chunks[1].chunk_id],
        ),
    ]

    minimal_output = ContentExtractionOutput(
        course_id=course_id,
        chunks=chunks,
        concepts=concepts,
    )

    designer = CourseDesigner()
    result = designer.generate_curriculum(minimal_output)

    # Must still adhere to Contract 2 minimum of 2 modules
    assert len(result.modules) == 2
    for mod in result.modules:
        assert len(mod.lessons) >= 1
        for lesson in mod.lessons:
            assert len(lesson.learning_objectives) >= 2


def test_llm_prompt_generation_and_fallback_parsing(mock_extraction_output: ContentExtractionOutput):
    """Verifies LLM prompt construction and resilient parsing fallback mechanism."""
    designer = CourseDesigner()

    # 1. Prompt generation
    prompt_dict = designer.generate_llm_prompt(mock_extraction_output)
    assert "system_instruction" in prompt_dict
    assert "user_prompt" in prompt_dict
    assert "Contract 2" in prompt_dict["system_instruction"]
    assert str(mock_extraction_output.course_id) in prompt_dict["user_prompt"]

    # 2. Resilient parsing on malformed LLM response -> falls back to deterministic generation
    malformed_response = "Here is the course outline: ```json { invalid_json ... ```"
    fallback_result = designer.parse_llm_response(malformed_response, mock_extraction_output)
    assert isinstance(fallback_result, CourseDesignOutput)
    assert len(fallback_result.modules) >= 2
