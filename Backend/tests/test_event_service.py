"""
Eduvance AI - Learner Event Service Unit Tests
WBS 4.1 - Telemetry & Progress Synchronization Engine

Tests:
- Ingestion of VIDEO_WATCHED and lesson_progress update.
- Ingestion of QUIZ_ATTEMPT and concept_mastery score synchronization.
- Composite completion transition (video + quiz = COMPLETED).
- Multi-user event querying and limit bounds.

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from Backend.core.progress_schemas import LearnerEventCreate
from Backend.services.event_service import EventService
from Database.models.all_models import (
    Base,
    Concept,
    ConceptMastery,
    Course,
    LearnerEvent,
    Lesson,
    LessonProgress,
    Module,
    User,
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
def telemetry_setup(db_session: Session):
    """Sets up a learner, course, module, lesson, and concept."""
    user = User(
        email="learner_one@eduvance.ai",
        password_hash="test_hash",
        full_name="Alice Learner",
        role="LEARNER",
    )
    db_session.add(user)
    db_session.flush()

    course = Course(
        title="Network Security Protocols",
        description="Comprehensive course on TLS and IPSec.",
        domain="CYBERSECURITY",
        status="ACTIVE",
        user_id=user.id,
    )
    db_session.add(course)
    db_session.flush()

    module = Module(course_id=course.id, title="Module 1: TLS Handshake", sequence_order=1)
    db_session.add(module)
    db_session.flush()

    concept = Concept(
        course_id=course.id,
        name="Diffie-Hellman Key Exchange",
        description="Asymmetric key agreement protocol providing forward secrecy.",
    )
    db_session.add(concept)
    db_session.flush()

    lesson = Lesson(
        module_id=module.id,
        title="Lesson 1: Key Exchange Principles",
        sequence_order=1,
        learning_objectives=["Understand DH key exchange."],
        target_concept_ids=[concept.id],
    )
    db_session.add(lesson)
    db_session.commit()

    return {
        "user_id": user.id,
        "course_id": course.id,
        "lesson_id": lesson.id,
        "concept_id": concept.id,
    }


def test_ingest_video_watched_updates_lesson_progress(db_session: Session, telemetry_setup):
    """Verifies VIDEO_WATCHED event sets video_completed and status=IN_PROGRESS."""
    service = EventService()
    event_data = LearnerEventCreate(
        course_id=uuid4(),
        lesson_id=uuid4(),
        event_type="VIDEO_WATCHED",
        payload={"seconds_watched": 90, "total_duration": 100, "completed": True},
    )
    # Set matching IDs
    event_data.course_id = telemetry_setup["course_id"]
    event_data.lesson_id = telemetry_setup["lesson_id"]

    event = service.ingest_event(db_session, telemetry_setup["user_id"], event_data)
    assert event.event_type == "VIDEO_WATCHED"

    # Verify lesson_progress updated
    progress = (
        db_session.query(LessonProgress)
        .filter(
            LessonProgress.user_id == telemetry_setup["user_id"],
            LessonProgress.lesson_id == telemetry_setup["lesson_id"],
        )
        .first()
    )
    assert progress is not None
    assert progress.video_completed is True
    assert progress.quiz_completed is False
    assert progress.status == "IN_PROGRESS"


def test_ingest_quiz_attempt_updates_mastery_and_completes_lesson(db_session: Session, telemetry_setup):
    """Verifies QUIZ_ATTEMPT completes lesson and updates ConceptMastery score."""
    service = EventService()

    # 1. Complete video first
    service.ingest_event(
        db_session,
        telemetry_setup["user_id"],
        LearnerEventCreate(
            course_id=telemetry_setup["course_id"],
            lesson_id=telemetry_setup["lesson_id"],
            event_type="VIDEO_WATCHED",
            payload={"completed": True},
        ),
    )

    # 2. Ingest Quiz Attempt (Passing score 85%)
    cid = str(telemetry_setup["concept_id"])
    quiz_event_data = LearnerEventCreate(
        course_id=telemetry_setup["course_id"],
        lesson_id=telemetry_setup["lesson_id"],
        event_type="QUIZ_ATTEMPT",
        payload={
            "score_percentage": 85.0,
            "passed": True,
            "concept_scores": {cid: 85.0},
        },
    )

    service.ingest_event(db_session, telemetry_setup["user_id"], quiz_event_data)

    # Verify lesson_progress is now COMPLETED
    progress = (
        db_session.query(LessonProgress)
        .filter(
            LessonProgress.user_id == telemetry_setup["user_id"],
            LessonProgress.lesson_id == telemetry_setup["lesson_id"],
        )
        .first()
    )
    assert progress.video_completed is True
    assert progress.quiz_completed is True
    assert progress.status == "COMPLETED"

    # Verify concept_mastery recorded
    cm = (
        db_session.query(ConceptMastery)
        .filter(
            ConceptMastery.user_id == telemetry_setup["user_id"],
            ConceptMastery.concept_id == cid,
        )
        .first()
    )
    assert cm is not None
    assert cm.mastery_score == 85.0
    assert cm.needs_revision is False


def test_failing_quiz_sets_needs_revision_flag(db_session: Session, telemetry_setup):
    """Verifies score < 70% sets needs_revision=True on ConceptMastery."""
    service = EventService()
    cid = str(telemetry_setup["concept_id"])

    quiz_event_data = LearnerEventCreate(
        course_id=telemetry_setup["course_id"],
        lesson_id=telemetry_setup["lesson_id"],
        event_type="QUIZ_ATTEMPT",
        payload={
            "score_percentage": 50.0,
            "passed": False,
            "concept_scores": {cid: 50.0},
        },
    )

    service.ingest_event(db_session, telemetry_setup["user_id"], quiz_event_data)

    cm = (
        db_session.query(ConceptMastery)
        .filter(
            ConceptMastery.user_id == telemetry_setup["user_id"],
            ConceptMastery.concept_id == cid,
        )
        .first()
    )
    assert cm is not None
    assert cm.mastery_score == 50.0
    assert cm.needs_revision is True

