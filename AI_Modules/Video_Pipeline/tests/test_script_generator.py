"""
Eduvance AI - Video Script Generator Tests
WBS 3.4 - Narration Scripting & Instructional Storyboarding

Tests:
- Synthesis of Contract 3 compliant slide outlines and narration scripts.
- Bounded slide count scaling [3, 8] and duration constraints (<= 420 seconds).
- Provenance linking (each slide links to an existing source chunk).
- First slide agenda & final slide summary conventions.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from uuid import uuid4
import pytest

from AI_Modules.Video_Pipeline.schemas import LessonVideoAssetOutput
from AI_Modules.Video_Pipeline.script_generator import VideoScriptGenerator


def test_generate_lesson_script_satisfies_contract_3(mock_video_lesson_data):
    """Verifies generated script meets all Contract 3 Pydantic constraints."""
    generator = VideoScriptGenerator()
    result = generator.generate_lesson_script(
        lesson_id=mock_video_lesson_data["lesson_id"],
        lesson_title=mock_video_lesson_data["lesson_title"],
        learning_objectives=mock_video_lesson_data["learning_objectives"],
        concepts=mock_video_lesson_data["concepts"],
        chunks=mock_video_lesson_data["chunks"],
    )

    assert isinstance(result, LessonVideoAssetOutput)
    assert result.lesson_id == mock_video_lesson_data["lesson_id"]
    assert 3 <= len(result.slides) <= 8
    assert 10 <= result.total_estimated_seconds <= 420

    # Verify individual slide constraints
    valid_chunk_ids = {c.chunk_id for c in mock_video_lesson_data["chunks"]}
    for idx, slide in enumerate(result.slides, start=1):
        assert slide.slide_number == idx
        assert len(slide.header) >= 3
        assert 2 <= len(slide.bullet_points) <= 5
        assert len(slide.narration_script) >= 20
        assert slide.source_chunk_id in valid_chunk_ids


def test_first_and_final_slide_conventions(mock_video_lesson_data):
    """Verifies Slide 1 is an overview and final slide is a summary."""
    generator = VideoScriptGenerator()
    result = generator.generate_lesson_script(
        lesson_id=mock_video_lesson_data["lesson_id"],
        lesson_title=mock_video_lesson_data["lesson_title"],
        learning_objectives=mock_video_lesson_data["learning_objectives"],
        concepts=mock_video_lesson_data["concepts"],
        chunks=mock_video_lesson_data["chunks"],
    )

    first_slide = result.slides[0]
    final_slide = result.slides[-1]

    assert "Overview" in first_slide.header or "Overview" in first_slide.bullet_points[0]
    assert "Summary" in final_slide.header or "Synthesis" in final_slide.bullet_points[0]


def test_custom_slide_count_bounds(mock_video_lesson_data):
    """Verifies slide count requests are strictly clamped within [3, 8]."""
    generator = VideoScriptGenerator()

    # Request 5 slides
    res_5 = generator.generate_lesson_script(
        lesson_id=mock_video_lesson_data["lesson_id"],
        lesson_title=mock_video_lesson_data["lesson_title"],
        learning_objectives=mock_video_lesson_data["learning_objectives"],
        concepts=mock_video_lesson_data["concepts"],
        chunks=mock_video_lesson_data["chunks"],
        num_slides=5,
    )
    assert len(res_5.slides) == 5

    # Request 10 slides (should clamp to max 8)
    res_10 = generator.generate_lesson_script(
        lesson_id=mock_video_lesson_data["lesson_id"],
        lesson_title=mock_video_lesson_data["lesson_title"],
        learning_objectives=mock_video_lesson_data["learning_objectives"],
        concepts=mock_video_lesson_data["concepts"],
        chunks=mock_video_lesson_data["chunks"],
        num_slides=10,
    )
    assert len(res_10.slides) == 8

    # Request 1 slide (should clamp to min 3)
    res_1 = generator.generate_lesson_script(
        lesson_id=mock_video_lesson_data["lesson_id"],
        lesson_title=mock_video_lesson_data["lesson_title"],
        learning_objectives=mock_video_lesson_data["learning_objectives"],
        concepts=mock_video_lesson_data["concepts"],
        chunks=mock_video_lesson_data["chunks"],
        num_slides=1,
    )
    assert len(res_1.slides) == 3


def test_script_generator_rejects_empty_chunks(mock_video_lesson_data):
    """Verifies generator raises ValueError when chunks are omitted."""
    generator = VideoScriptGenerator()
    with pytest.raises(ValueError) as exc_info:
        generator.generate_lesson_script(
            lesson_id=mock_video_lesson_data["lesson_id"],
            lesson_title=mock_video_lesson_data["lesson_title"],
            learning_objectives=mock_video_lesson_data["learning_objectives"],
            concepts=mock_video_lesson_data["concepts"],
            chunks=[],
        )
    assert "source chunks" in str(exc_info.value)
