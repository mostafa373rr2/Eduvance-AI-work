"""
Eduvance AI - Course Design Schema Conformance Tests
WBS 3.3 - Step 1 Test Suite: Contract 2 Verification

Tests strict validation constraints of:
- LessonDesign (Bloom's objectives count, estimated_minutes [5, 30], target concepts)
- ModuleDesign (lessons count [1, 3], sequence indices)
- CourseDesignOutput (modules count [2, 4], min length bounds)

Owner: Member 2 (Content and RAG Engineer)
"""

from uuid import uuid4
import pytest
from pydantic import ValidationError

from AI_Modules.CourseDesign.schemas import (
    CourseDesignOutput,
    LessonDesign,
    LessonUpdate,
    ModuleDesign,
    ModuleUpdate,
)


def test_lesson_design_valid():
    """Valid lesson design satisfies Contract 2 schema."""
    lesson = LessonDesign(
        lesson_sequence=1,
        title="Foundations of Cybersecurity",
        estimated_minutes=15,
        learning_objectives=[
            "Identify key principles of cybersecurity governance.",
            "Explain the difference between threats and vulnerabilities.",
        ],
        target_concept_ids=[uuid4()],
        source_chunk_ids=[uuid4()],
    )
    assert lesson.lesson_sequence == 1
    assert lesson.estimated_minutes == 15
    assert len(lesson.learning_objectives) == 2


def test_lesson_design_estimated_minutes_bounds():
    """estimated_minutes must be clamped between 5 and 30 minutes."""
    # Below 5 minutes
    with pytest.raises(ValidationError) as exc_info:
        LessonDesign(
            lesson_sequence=1,
            title="Fast Lesson",
            estimated_minutes=4,
            learning_objectives=["Obj 1", "Obj 2"],
            target_concept_ids=[uuid4()],
            source_chunk_ids=[uuid4()],
        )
    assert "estimated_minutes" in str(exc_info.value)

    # Above 30 minutes
    with pytest.raises(ValidationError) as exc_info:
        LessonDesign(
            lesson_sequence=1,
            title="Long Lesson",
            estimated_minutes=35,
            learning_objectives=["Obj 1", "Obj 2"],
            target_concept_ids=[uuid4()],
            source_chunk_ids=[uuid4()],
        )
    assert "estimated_minutes" in str(exc_info.value)


def test_lesson_design_learning_objectives_min_length():
    """Every lesson must include at least 2 learning objectives."""
    with pytest.raises(ValidationError) as exc_info:
        LessonDesign(
            lesson_sequence=1,
            title="Single Objective Lesson",
            estimated_minutes=10,
            learning_objectives=["Only one objective."],
            target_concept_ids=[uuid4()],
            source_chunk_ids=[uuid4()],
        )
    assert "learning_objectives" in str(exc_info.value)


def test_module_design_lessons_count_bounds():
    """Modules must contain between 1 and 3 lessons."""
    dummy_lesson = LessonDesign(
        lesson_sequence=1,
        title="Lesson Title",
        estimated_minutes=10,
        learning_objectives=["Obj 1", "Obj 2"],
        target_concept_ids=[uuid4()],
        source_chunk_ids=[uuid4()],
    )

    # 0 lessons rejected
    with pytest.raises(ValidationError) as exc_info:
        ModuleDesign(
            module_sequence=1,
            title="Empty Module",
            description="Module with no lessons provided.",
            lessons=[],
        )
    assert "lessons" in str(exc_info.value)

    # > 3 lessons rejected
    with pytest.raises(ValidationError) as exc_info:
        ModuleDesign(
            module_sequence=1,
            title="Overcrowded Module",
            description="Module with four lessons exceeds max limit.",
            lessons=[dummy_lesson, dummy_lesson, dummy_lesson, dummy_lesson],
        )
    assert "lessons" in str(exc_info.value)


def test_course_design_output_modules_bounds():
    """Course must contain between 2 and 4 modules."""
    lesson = LessonDesign(
        lesson_sequence=1,
        title="Lesson Title",
        estimated_minutes=10,
        learning_objectives=["Obj 1", "Obj 2"],
        target_concept_ids=[uuid4()],
        source_chunk_ids=[uuid4()],
    )
    module = ModuleDesign(
        module_sequence=1,
        title="Module Title",
        description="Module description for testing bounds.",
        lessons=[lesson],
    )

    # 1 module rejected (min is 2)
    with pytest.raises(ValidationError) as exc_info:
        CourseDesignOutput(
            course_title="Test Course Title",
            description="Comprehensive course overview description for testing purposes.",
            modules=[module],
        )
    assert "modules" in str(exc_info.value)

    # 5 modules rejected (max is 4)
    with pytest.raises(ValidationError) as exc_info:
        CourseDesignOutput(
            course_title="Test Course Title",
            description="Comprehensive course overview description for testing purposes.",
            modules=[module, module, module, module, module],
        )
    assert "modules" in str(exc_info.value)


def test_course_design_output_title_and_description_min_length():
    """Course title must be >= 5 chars, description >= 20 chars."""
    lesson = LessonDesign(
        lesson_sequence=1,
        title="Lesson Title",
        estimated_minutes=10,
        learning_objectives=["Obj 1", "Obj 2"],
        target_concept_ids=[uuid4()],
        source_chunk_ids=[uuid4()],
    )
    module = ModuleDesign(
        module_sequence=1,
        title="Module Title",
        description="Module description for testing bounds.",
        lessons=[lesson],
    )

    # Title too short (< 5)
    with pytest.raises(ValidationError):
        CourseDesignOutput(
            course_title="AI",
            description="A valid description that is definitely longer than twenty characters.",
            modules=[module, module],
        )

    # Description too short (< 20)
    with pytest.raises(ValidationError):
        CourseDesignOutput(
            course_title="Valid Course Title",
            description="Too short desc.",
            modules=[module, module],
        )


def test_instructor_update_schemas():
    """Tests LessonUpdate and ModuleUpdate instructor edit models."""
    l_up = LessonUpdate(title="Revised Lesson Title", estimated_minutes=25)
    assert l_up.title == "Revised Lesson Title"
    assert l_up.estimated_minutes == 25
    assert l_up.learning_objectives is None

    m_up = ModuleUpdate(title="Revised Module Title")
    assert m_up.title == "Revised Module Title"
    assert m_up.description is None
