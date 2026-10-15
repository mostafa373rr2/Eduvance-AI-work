"""
Eduvance AI - Video Pipeline Schema Conformance Tests
WBS 3.4 - Step 1 Test Suite: Contract 3 Verification

Tests strict validation constraints of:
- SlideSpec (header length, bullet points [2, 5], narration script min length)
- LessonVideoAssetOutput (slides [3, 8], total_estimated_seconds <= 420)

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from uuid import uuid4
import pytest
from pydantic import ValidationError

from AI_Modules.Video_Pipeline.schemas import (
    LessonVideoAssetOutput,
    RenderedSlide,
    SlideSpec,
    SubtitleEntry,
    VideoPackageResult,
)


def test_slide_spec_valid():
    """Valid slide specification satisfies Contract 3 schema."""
    slide = SlideSpec(
        slide_number=1,
        header="Introduction to Zero Trust",
        bullet_points=[
            "Never trust, always verify every access request.",
            "Enforce least-privilege access dynamically.",
        ],
        visual_cue="Zero Trust Architectural Framework Diagram",
        narration_script="Welcome to this lesson on Zero Trust architecture and defense-in-depth principles.",
        source_chunk_id=uuid4(),
    )
    assert slide.slide_number == 1
    assert len(slide.bullet_points) == 2
    assert len(slide.narration_script) >= 20


def test_slide_spec_bullet_points_bounds():
    """bullet_points must contain between 2 and 5 points."""
    # < 2 bullets rejected
    with pytest.raises(ValidationError) as exc_info:
        SlideSpec(
            slide_number=1,
            header="Single Bullet Slide",
            bullet_points=["Only one point here."],
            narration_script="Valid narration script that easily exceeds the twenty character minimum length.",
            source_chunk_id=uuid4(),
        )
    assert "bullet_points" in str(exc_info.value)

    # > 5 bullets rejected
    with pytest.raises(ValidationError) as exc_info:
        SlideSpec(
            slide_number=1,
            header="Overcrowded Slide",
            bullet_points=["P1", "P2", "P3", "P4", "P5", "P6"],
            narration_script="Valid narration script that easily exceeds the twenty character minimum length.",
            source_chunk_id=uuid4(),
        )
    assert "bullet_points" in str(exc_info.value)


def test_slide_spec_narration_script_min_length():
    """narration_script must be at least 20 characters."""
    with pytest.raises(ValidationError) as exc_info:
        SlideSpec(
            slide_number=1,
            header="Short Narration Slide",
            bullet_points=["Point 1", "Point 2"],
            narration_script="Too short script.",  # 17 chars (< 20)
            source_chunk_id=uuid4(),
        )
    assert "narration_script" in str(exc_info.value)


def test_lesson_video_asset_output_valid():
    """Valid LessonVideoAssetOutput satisfies root Contract 3."""
    dummy_slide = SlideSpec(
        slide_number=1,
        header="Slide Header",
        bullet_points=["Point A", "Point B"],
        narration_script="Detailed narration script meeting minimum length requirements.",
        source_chunk_id=uuid4(),
    )

    output = LessonVideoAssetOutput(
        lesson_id=uuid4(),
        total_estimated_seconds=120,
        slides=[dummy_slide, dummy_slide, dummy_slide],
    )
    assert len(output.slides) == 3
    assert output.total_estimated_seconds == 120


def test_lesson_video_asset_output_slides_bounds():
    """slides count must be between 3 and 8."""
    dummy_slide = SlideSpec(
        slide_number=1,
        header="Slide Header",
        bullet_points=["Point A", "Point B"],
        narration_script="Detailed narration script meeting minimum length requirements.",
        source_chunk_id=uuid4(),
    )

    # < 3 slides rejected
    with pytest.raises(ValidationError) as exc_info:
        LessonVideoAssetOutput(
            lesson_id=uuid4(),
            total_estimated_seconds=60,
            slides=[dummy_slide, dummy_slide],
        )
    assert "slides" in str(exc_info.value)

    # > 8 slides rejected
    with pytest.raises(ValidationError) as exc_info:
        LessonVideoAssetOutput(
            lesson_id=uuid4(),
            total_estimated_seconds=300,
            slides=[dummy_slide] * 9,
        )
    assert "slides" in str(exc_info.value)


def test_lesson_video_asset_output_max_duration():
    """total_estimated_seconds must not exceed 420 seconds (7 minutes)."""
    dummy_slide = SlideSpec(
        slide_number=1,
        header="Slide Header",
        bullet_points=["Point A", "Point B"],
        narration_script="Detailed narration script meeting minimum length requirements.",
        source_chunk_id=uuid4(),
    )

    with pytest.raises(ValidationError) as exc_info:
        LessonVideoAssetOutput(
            lesson_id=uuid4(),
            total_estimated_seconds=450,  # > 420
            slides=[dummy_slide, dummy_slide, dummy_slide],
        )
    assert "total_estimated_seconds" in str(exc_info.value)


def test_rendered_slide_and_subtitle_schemas():
    """Tests RenderedSlide and SubtitleEntry models."""
    rs = RenderedSlide(slide_number=1, image_path="/path/to/slide.png")
    assert rs.width == 1920
    assert rs.height == 1080

    sub = SubtitleEntry(index=1, start_seconds=0.0, end_seconds=4.25, text="Hello world")
    assert sub.index == 1
    assert sub.end_seconds == 4.25
