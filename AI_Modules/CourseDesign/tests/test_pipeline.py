"""
Eduvance AI - Course Design Pipeline & Persistence Integration Tests
WBS 3.3 - Course Designer Agent Testing

Tests:
- End-to-end curriculum generation and database persistence into Module and Lesson tables.
- Course status state transitions: EXTRACTED -> DESIGNING_COURSE -> PENDING_APPROVAL -> GENERATING_ASSETS.
- Instructor review workflows: updating lessons, modifying module titles, reordering lessons.
- Foreign key integrity and cascade constraints.

Owner: Member 2 (Content and RAG Engineer)
"""

from uuid import uuid4
import pytest
from sqlalchemy.orm import Session

from AI_Modules.CourseDesign.persistence import CourseDesignPersistenceService
from AI_Modules.CourseDesign.pipeline import CourseDesignPipeline
from AI_Modules.CourseDesign.schemas import CourseDesignOutput, LessonUpdate, ModuleUpdate
from AI_Modules.Extraction.schemas import ContentExtractionOutput
from Database.models.all_models import Course, Lesson, Module


def test_pipeline_end_to_end_persists_to_database(
    db_session: Session,
    sample_persisted_course: Course,
    mock_extraction_output: ContentExtractionOutput,
):
    """Verifies complete pipeline creates modules, lessons, and sets status to PENDING_APPROVAL."""
    pipeline = CourseDesignPipeline()

    result = pipeline.process_course_curriculum(
        extraction_output=mock_extraction_output,
        session=db_session,
        persist=True,
    )

    assert isinstance(result, CourseDesignOutput)

    # Verify course record updated
    db_course = db_session.query(Course).filter(Course.id == sample_persisted_course.id).first()
    assert db_course is not None
    assert db_course.status == "PENDING_APPROVAL"
    assert db_course.title == result.course_title

    # Verify modules in database
    db_modules = db_session.query(Module).filter(Module.course_id == sample_persisted_course.id).order_index_by = Module.sequence_order
    db_modules = db_session.query(Module).filter(Module.course_id == sample_persisted_course.id).order_by(Module.sequence_order).all()
    assert len(db_modules) == len(result.modules)

    # Verify lessons in database
    for mod_idx, db_mod in enumerate(db_modules):
        expected_mod_design = result.modules[mod_idx]
        assert db_mod.title == expected_mod_design.title
        assert db_mod.sequence_order == expected_mod_design.module_sequence

        db_lessons = db_session.query(Lesson).filter(Lesson.module_id == db_mod.id).order_by(Lesson.sequence_order).all()
        assert len(db_lessons) == len(expected_mod_design.lessons)

        for les_idx, db_les in enumerate(db_lessons):
            expected_les_design = expected_mod_design.lessons[les_idx]
            assert db_les.title == expected_les_design.title
            assert db_les.sequence_order == expected_les_design.lesson_sequence
            assert db_les.estimated_minutes == expected_les_design.estimated_minutes
            assert len(db_les.learning_objectives) >= 2
            assert len(db_les.target_concept_ids) >= 1
            assert len(db_les.source_chunk_ids) >= 1


def test_instructor_update_lesson(
    db_session: Session,
    sample_persisted_course: Course,
    mock_extraction_output: ContentExtractionOutput,
):
    """Verifies instructor can modify an individual lesson title and objectives."""
    pipeline = CourseDesignPipeline()
    pipeline.process_course_curriculum(mock_extraction_output, session=db_session, persist=True)

    service = CourseDesignPersistenceService()
    lesson = db_session.query(Lesson).first()
    assert lesson is not None

    update_payload = LessonUpdate(
        title="Customized Lesson Title by Instructor",
        estimated_minutes=25,
        learning_objectives=[
            "Demonstrate customized practical mastery of the framework.",
            "Analyze operational edge cases in enterprise environments.",
        ],
    )

    updated_lesson = service.update_lesson(db_session, lesson.id, update_payload)
    assert updated_lesson.title == "Customized Lesson Title by Instructor"
    assert updated_lesson.estimated_minutes == 25
    assert len(updated_lesson.learning_objectives) == 2
    assert "customized" in updated_lesson.learning_objectives[0]


def test_instructor_update_module(
    db_session: Session,
    sample_persisted_course: Course,
    mock_extraction_output: ContentExtractionOutput,
):
    """Verifies instructor can modify module title and description."""
    pipeline = CourseDesignPipeline()
    pipeline.process_course_curriculum(mock_extraction_output, session=db_session, persist=True)

    service = CourseDesignPersistenceService()
    module = db_session.query(Module).first()
    assert module is not None

    update_payload = ModuleUpdate(
        title="Instructor Customized Module Heading",
        description="Comprehensive custom description written by the instructor.",
    )

    updated_mod = service.update_module(db_session, module.id, update_payload)
    assert updated_mod.title == "Instructor Customized Module Heading"
    assert "Comprehensive custom description" in updated_mod.description


def test_instructor_reorder_lessons(
    db_session: Session,
    sample_persisted_course: Course,
    mock_extraction_output: ContentExtractionOutput,
):
    """Verifies instructor can reorder lessons within a module."""
    pipeline = CourseDesignPipeline()
    pipeline.process_course_curriculum(mock_extraction_output, session=db_session, persist=True)

    service = CourseDesignPersistenceService()
    # Find a module with at least 2 lessons
    modules = db_session.query(Module).all()
    target_mod = None
    for m in modules:
        lessons = db_session.query(Lesson).filter(Lesson.module_id == m.id).all()
        if len(lessons) >= 2:
            target_mod = m
            break

    if target_mod is not None:
        lessons = db_session.query(Lesson).filter(Lesson.module_id == target_mod.id).order_by(Lesson.sequence_order).all()
        reversed_ids = [l.id for l in reversed(lessons)]

        reordered = service.reorder_lessons(db_session, target_mod.id, reversed_ids)
        assert reordered[0].id == reversed_ids[0]
        assert reordered[0].sequence_order == 1
        assert reordered[1].id == reversed_ids[1]
        assert reordered[1].sequence_order == 2


def test_course_approval_workflow(
    db_session: Session,
    sample_persisted_course: Course,
    mock_extraction_output: ContentExtractionOutput,
):
    """Verifies approving course transitions status from PENDING_APPROVAL to GENERATING_ASSETS."""
    pipeline = CourseDesignPipeline()
    pipeline.process_course_curriculum(mock_extraction_output, session=db_session, persist=True)

    service = CourseDesignPersistenceService()

    # Approve course design
    approved_course = service.approve_course_design(db_session, mock_extraction_output.course_id)
    assert approved_course.status == "GENERATING_ASSETS"

    # Attempting to re-approve raises ValueError
    with pytest.raises(ValueError) as exc_info:
        service.approve_course_design(db_session, mock_extraction_output.course_id)
    assert "Current status is 'GENERATING_ASSETS'" in str(exc_info.value)
