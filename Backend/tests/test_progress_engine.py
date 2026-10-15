"""
Eduvance AI - Progress & Recommendation Engine Unit Tests
WBS 4.1 - Contract 6 Conformance & Remedial Logic

Tests:
- Generation of Contract 6 compliant ProgressEvaluationOutput.
- Calculation of overall completion percentage (completed lessons / total lessons).
- Concept mastery score aggregation.
- Explainable recommendation formulation when score < 70%.

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from uuid import UUID, uuid4
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from Backend.core.progress_schemas import ProgressEvaluationOutput
from Backend.services.progress_engine import ProgressEngine
from Database.models.all_models import (
    Base,
    Concept,
    ConceptMastery,
    Course,
    Lesson,
    LessonProgress,
    Module,
    User,
    _utcnow,
)


@pytest.fixture
def db_session():
    """In-memory SQLite session with full schema initialized."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def progress_test_data(db_session: Session):
    """Sets up a complete learner, course, 2 lessons, and 2 concepts."""
    user = User(
        email="bob_learner@eduvance.ai",
        password_hash="test_hash",
        full_name="Bob Student",
        role="LEARNER",
    )
    db_session.add(user)
    db_session.flush()

    course = Course(
        title="Applied Cloud Engineering",
        description="Comprehensive course on container orchestration.",
        domain="DEVOPS",
        status="ACTIVE",
        user_id=user.id,
    )
    db_session.add(course)
    db_session.flush()

    module = Module(course_id=course.id, title="Module 1: Kubernetes Core", sequence_order=1)
    db_session.add(module)
    db_session.flush()

    # Concept 1 (Mastered, 85%)
    c1 = Concept(
        course_id=course.id,
        name="Pod Networking & CNI",
        description="Overlay networking and IPAM across Kubernetes worker nodes.",
    )
    # Concept 2 (Weak, 55% - Needs Revision)
    c2 = Concept(
        course_id=course.id,
        name="Ingress Controllers & TLS",
        description="Reverse proxy routing rules and automated certificate termination.",
    )
    db_session.add_all([c1, c2])
    db_session.flush()

    # Lesson 1 (Completed)
    l1 = Lesson(
        module_id=module.id,
        title="Lesson 1: Pod Networking",
        sequence_order=1,
        learning_objectives=["Understand CNI."],
        target_concept_ids=[c1.id],
    )
    # Lesson 2 (In Progress)
    l2 = Lesson(
        module_id=module.id,
        title="Lesson 2: Ingress & TLS",
        sequence_order=2,
        learning_objectives=["Configure ingress routes."],
        target_concept_ids=[c2.id],
    )
    db_session.add_all([l1, l2])
    db_session.flush()

    # Progress: L1 is COMPLETED, L2 is IN_PROGRESS
    lp1 = LessonProgress(
        user_id=user.id,
        lesson_id=l1.id,
        status="COMPLETED",
        video_completed=True,
        quiz_completed=True,
    )
    lp2 = LessonProgress(
        user_id=user.id,
        lesson_id=l2.id,
        status="IN_PROGRESS",
        video_completed=True,
        quiz_completed=False,
    )
    db_session.add_all([lp1, lp2])

    # Mastery: C1 is 85%, C2 is 55%
    cm1 = ConceptMastery(
        user_id=user.id,
        concept_id=c1.id,
        mastery_score=85.0,
        needs_revision=False,
        last_evaluated_at=_utcnow(),
    )
    cm2 = ConceptMastery(
        user_id=user.id,
        concept_id=c2.id,
        mastery_score=55.0,
        needs_revision=True,
        last_evaluated_at=_utcnow(),
    )
    db_session.add_all([cm1, cm2])
    db_session.commit()

    return {
        "user_id": UUID(user.id),
        "course_id": UUID(course.id),
        "l1_id": UUID(l1.id),
        "l2_id": UUID(l2.id),
        "c1_id": UUID(c1.id),
        "c2_id": UUID(c2.id),
    }


def test_progress_engine_contract_6_evaluation(db_session: Session, progress_test_data):
    """Verifies that progress evaluation strictly conforms to Contract 6."""
    engine = ProgressEngine()
    result = engine.evaluate_course_progress(
        session=db_session,
        user_id=progress_test_data["user_id"],
        course_id=progress_test_data["course_id"],
    )

    assert isinstance(result, ProgressEvaluationOutput)
    assert result.user_id == progress_test_data["user_id"]
    assert result.course_id == progress_test_data["course_id"]

    # 1 out of 2 lessons completed = 50.0%
    assert result.overall_completion_percentage == 50.0

    # Concepts summary
    assert len(result.concept_mastery_summary) == 2
    c1_summary = next(c for c in result.concept_mastery_summary if c.concept_id == progress_test_data["c1_id"])
    c2_summary = next(c for c in result.concept_mastery_summary if c.concept_id == progress_test_data["c2_id"])

    assert c1_summary.score_percentage == 85.0
    assert c1_summary.needs_revision is False

    assert c2_summary.score_percentage == 55.0
    assert c2_summary.needs_revision is True

    # Recommendations: C2 scored 55% (< 70%), so exactly 1 recommendation triggered
    assert len(result.recommendations) == 1
    rec = result.recommendations[0]
    assert rec.lesson_id == progress_test_data["l2_id"]
    assert rec.trigger_concept == "Ingress Controllers & TLS"
    assert rec.trigger_quiz_score == 55.0
    assert "Remedial revision recommended" in rec.reason
    assert "Ingress Controllers & TLS" in rec.reason

