"""
Eduvance AI - Video Pipeline Test Fixtures
WBS 3.4 - Video Agent Testing

Provides standard fixtures for video generation tests:
- Synthetic lesson data with learning objectives and target concepts.
- Extraction chunks and concepts.
- In-memory SQLite session with Course, Module, and Lesson models.
- Temporary output directory fixture.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from pathlib import Path
import shutil
import tempfile
from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from AI_Modules.Extraction.schemas import DifficultyLevel, ExtractedChunk, ExtractedConcept
from Database.models.all_models import Base, Course, Lesson, Module, User


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Provides a clean temporary directory for rendering images, audio, and subtitles."""
    dir_path = Path(tempfile.mkdtemp(prefix="eduvance_video_test_"))
    yield dir_path
    shutil.rmtree(dir_path, ignore_errors=True)


@pytest.fixture
def mock_video_lesson_data():
    """Provides structured lesson, concept, and chunk metadata for video generation."""
    lesson_id = uuid4()
    doc_id = uuid4()

    chunks = [
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            page_number=1,
            section_header="1. Identity Governance Architecture",
            text_content=(
                "Identity governance defines authentication frameworks, cryptographic credential issuance, "
                "and federated authorization policies across organizational boundaries."
            ),
            token_count=130,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=1,
            page_number=2,
            section_header="1.1 Least Privilege & RBAC",
            text_content=(
                "Role-based access control enforces least privilege by limiting resource access strictly "
                "to what is required for a user's defined organizational responsibilities."
            ),
            token_count=140,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=2,
            page_number=3,
            section_header="1.2 Multi-Factor Authentication",
            text_content=(
                "Multi-factor authentication requires two or more verification factors, drastically reducing "
                "the likelihood of successful unauthorized account takeover."
            ),
            token_count=135,
        ),
    ]

    concepts = [
        ExtractedConcept(
            concept_id=uuid4(),
            name="Identity Governance",
            description="Centralized authentication policies and credential lifecycle management.",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisite_names=[],
            source_chunk_ids=[chunks[0].chunk_id],
        ),
        ExtractedConcept(
            concept_id=uuid4(),
            name="Least Privilege Access",
            description="Restricting user access permissions to minimal necessary operational capabilities.",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisite_names=["Identity Governance"],
            source_chunk_ids=[chunks[1].chunk_id],
        ),
    ]

    learning_objectives = [
        "Explain the fundamental mechanisms and policies of identity governance.",
        "Implement role-based access control under the principle of least privilege.",
    ]

    return {
        "lesson_id": lesson_id,
        "lesson_title": "Identity Governance & Access Control",
        "learning_objectives": learning_objectives,
        "concepts": concepts,
        "chunks": chunks,
    }


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """In-memory SQLite database session fixture with initialized schema."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def persisted_db_lesson(db_session: Session, mock_video_lesson_data) -> Lesson:
    """Creates and commits User, Course, Module, and Lesson in the DB session."""
    user = User(
        email="instructor_video@eduvance.ai",
        password_hash="test_bcrypt_hash",
        full_name="Prof. David Video",
        role="INSTRUCTOR",
    )
    db_session.add(user)
    db_session.flush()

    course = Course(
        title="Advanced Cybersecurity Architecture",
        description="Comprehensive course exploring enterprise security engineering.",
        domain="CYBERSECURITY",
        status="GENERATING_ASSETS",
        user_id=user.id,
    )
    db_session.add(course)
    db_session.flush()

    module = Module(
        course_id=course.id,
        title="Module 1: Identity & Access Management",
        sequence_order=1,
        description="Foundations of identity governance and access control.",
    )
    db_session.add(module)
    db_session.flush()

    lesson = Lesson(
        id=str(mock_video_lesson_data["lesson_id"]),
        module_id=module.id,
        title=mock_video_lesson_data["lesson_title"],
        sequence_order=1,
        estimated_minutes=15,
        learning_objectives=mock_video_lesson_data["learning_objectives"],
        target_concept_ids=[str(c.concept_id) for c in mock_video_lesson_data["concepts"]],
        source_chunk_ids=[str(ch.chunk_id) for ch in mock_video_lesson_data["chunks"]],
    )
    db_session.add(lesson)
    db_session.commit()

    return lesson
