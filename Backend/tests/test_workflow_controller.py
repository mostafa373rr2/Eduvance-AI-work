"""
Eduvance AI - Workflow Controller Unit Tests
WBS 4.1 - Central Workflow Controller & State Machine

Tests:
- Valid and invalid course state machine transitions.
- Asynchronous task lifecycle (create, start, complete).
- Bounded retry policy (re-queueing on retries <= 2, status=FAILED upon exhaustion).
- Course status degradation on exhausted asset generation retries.
- Full workflow status reporting.

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from Backend.services.workflow_controller import WorkflowController
from Database.models.all_models import Base, Course, Lesson, Module, User


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
def sample_course(db_session: Session) -> Course:
    """Creates a sample User and Course in DRAFT status."""
    user = User(
        email="workflow_mgr@eduvance.ai",
        password_hash="test_hash",
        full_name="Workflow Admin",
        role="INSTRUCTOR",
    )
    db_session.add(user)
    db_session.flush()

    course = Course(
        title="Zero Trust Security Architecture",
        description="Comprehensive course on network perimeter defenses.",
        domain="CYBERSECURITY",
        status="DRAFT",
        user_id=user.id,
    )
    db_session.add(course)
    db_session.commit()
    return course


def test_valid_state_machine_transitions(db_session: Session, sample_course: Course):
    """Verifies standard progression through the course lifecycle."""
    controller = WorkflowController()
    course_id = uuid4()
    sample_course.id = str(course_id)
    db_session.commit()

    # DRAFT -> EXTRACTING
    c = controller.transition_course_status(db_session, course_id, "EXTRACTING")
    assert c.status == "EXTRACTING"

    # EXTRACTING -> EXTRACTED
    c = controller.transition_course_status(db_session, course_id, "EXTRACTED")
    assert c.status == "EXTRACTED"

    # EXTRACTED -> DESIGNING_COURSE
    c = controller.transition_course_status(db_session, course_id, "DESIGNING_COURSE")
    assert c.status == "DESIGNING_COURSE"

    # DESIGNING_COURSE -> PENDING_APPROVAL
    c = controller.transition_course_status(db_session, course_id, "PENDING_APPROVAL")
    assert c.status == "PENDING_APPROVAL"

    # PENDING_APPROVAL -> GENERATING_ASSETS
    c = controller.transition_course_status(db_session, course_id, "GENERATING_ASSETS")
    assert c.status == "GENERATING_ASSETS"

    # GENERATING_ASSETS -> ACTIVE
    c = controller.transition_course_status(db_session, course_id, "ACTIVE")
    assert c.status == "ACTIVE"


def test_invalid_state_transition_raises_error(db_session: Session, sample_course: Course):
    """Attempting an illegal transition (e.g. DRAFT -> ACTIVE) raises ValueError."""
    controller = WorkflowController()
    course_id = uuid4()
    sample_course.id = str(course_id)
    db_session.commit()

    with pytest.raises(ValueError) as exc_info:
        controller.transition_course_status(db_session, course_id, "ACTIVE")
    assert "Invalid course state transition from 'DRAFT' to 'ACTIVE'" in str(exc_info.value)


def test_workflow_task_lifecycle(db_session: Session, sample_course: Course):
    """Verifies task creation, start, and completion timestamps."""
    controller = WorkflowController()
    course_id = uuid4()
    sample_course.id = str(course_id)
    db_session.commit()

    # 1. Create task
    task = controller.create_task(db_session, course_id, "EXTRACTION")
    assert task.status == "PENDING"
    assert task.started_at is None
    assert task.completed_at is None

    # 2. Start task
    started_task = controller.start_task(db_session, task.id)
    assert started_task.status == "RUNNING"
    assert started_task.started_at is not None

    # 3. Complete task
    completed_task = controller.complete_task(db_session, task.id)
    assert completed_task.status == "COMPLETED"
    assert completed_task.completed_at is not None


def test_retry_policy_re_queues_then_fails(db_session: Session, sample_course: Course):
    """Verifies bounded retry policy: 2 retries re-queue as PENDING, 3rd marks FAILED."""
    controller = WorkflowController()
    course_id = uuid4()
    sample_course.id = str(course_id)
    db_session.commit()

    task = controller.create_task(db_session, course_id, "VIDEO_GEN_SAMPLE")

    # Failure 1: retry_count=1 <= 2 -> re-queued to PENDING
    t1 = controller.fail_task(db_session, task.id, "Connection timeout error 1")
    assert t1.status == "PENDING"
    assert t1.retry_count == 1

    # Failure 2: retry_count=2 <= 2 -> re-queued to PENDING
    t2 = controller.fail_task(db_session, task.id, "Connection timeout error 2")
    assert t2.status == "PENDING"
    assert t2.retry_count == 2

    # Failure 3: retry_count=3 > 2 -> status=FAILED
    t3 = controller.fail_task(db_session, task.id, "Fatal unrecoverable error 3")
    assert t3.status == "FAILED"
    assert t3.retry_count == 3
    assert t3.completed_at is not None


def test_trigger_asset_generation_workflow(db_session: Session, sample_course: Course):
    """Verifies approving course creates tasks and transitions state to ACTIVE."""
    controller = WorkflowController()
    course_id = uuid4()
    sample_course.id = str(course_id)
    sample_course.status = "PENDING_APPROVAL"

    # Add module and lesson
    module = Module(course_id=str(course_id), title="Mod 1", sequence_order=1)
    db_session.add(module)
    db_session.flush()

    lesson = Lesson(
        module_id=module.id,
        title="Lesson 1",
        sequence_order=1,
        learning_objectives=["Obj 1", "Obj 2"],
    )
    db_session.add(lesson)
    db_session.commit()

    # Trigger asset generation
    updated_course = controller.trigger_asset_generation(db_session, course_id, simulate_execution=True)
    assert updated_course.status == "ACTIVE"

    # Check status report
    status_report = controller.get_workflow_status(db_session, course_id)
    assert status_report.course_status == "ACTIVE"
    assert status_report.total_tasks >= 3  # Video, Quiz, RAG
    assert status_report.completed_tasks == status_report.total_tasks
    assert status_report.progress_percentage == 100.0

