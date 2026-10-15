"""
Eduvance AI - Assessment Test Fixtures
WBS 3.5 - Assessment Agent Testing

Provides standard fixtures for assessment generation and evaluation tests:
- Synthetic lesson data with learning objectives and target concepts.
- Extraction chunks and concepts.
- In-memory SQLite session with Course, Module, and Lesson models.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from AI_Modules.Extraction.schemas import DifficultyLevel, ExtractedChunk, ExtractedConcept
from Database.models.all_models import Base, Course, Lesson, Module, User


@pytest.fixture
def mock_assessment_lesson_data():
    """Provides structured lesson, concept, and chunk metadata for assessment tests."""
    lesson_id = uuid4()
    doc_id = uuid4()

    chunks = [
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            page_number=1,
            section_header="1. Cryptographic Key Management",
            text_content=(
                "Key management governs the generation, exchange, storage, and retirement of cryptographic keys. "
                "Hardware Security Modules provide tamper-resistant cryptographic isolation."
            ),
            token_count=135,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=1,
            page_number=2,
            section_header="1.1 Key Rotation Policies",
            text_content=(
                "Automated periodic key rotation mitigates cryptanalytic exposure by limiting the volume of ciphertext "
                "encrypted under a single master key."
            ),
            token_count=145,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=2,
            page_number=3,
            section_header="1.2 Zero Knowledge Encryption",
            text_content=(
                "Zero knowledge architectures ensure that cloud service providers cannot access plaintext client keys "
                "or decrypt stored tenant data."
            ),
            token_count=140,
        ),
    ]

    concepts = [
        ExtractedConcept(
            concept_id=uuid4(),
            name="Cryptographic Key Management",
            description="Lifecycle policies and hardware safeguards for cryptographic materials.",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisite_names=[],
            source_chunk_ids=[chunks[0].chunk_id],
        ),
        ExtractedConcept(
            concept_id=uuid4(),
            name="Automated Key Rotation",
            description="Periodic retirement and re-encryption procedures to bound cryptographic exposure.",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisite_names=["Cryptographic Key Management"],
            source_chunk_ids=[chunks[1].chunk_id],
        ),
    ]

    learning_objectives = [
        "Explain the lifecycle stages of cryptographic key management.",
        "Implement automated key rotation policies within cloud infrastructure.",
    ]

    return {
        "lesson_id": lesson_id,
        "lesson_title": "Cryptographic Key Management & Rotation",
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
def persisted_db_lesson(db_session: Session, mock_assessment_lesson_data) -> Lesson:
    """Creates and commits User, Course, Module, and Lesson in the DB session."""
    user = User(
        email="instructor_assessment@eduvance.ai",
        password_hash="test_bcrypt_hash",
        full_name="Dr. Alice Assessment",
        role="INSTRUCTOR",
    )
    db_session.add(user)
    db_session.flush()

    course = Course(
        title="Applied Cryptography & Security Engineering",
        description="Comprehensive course exploring cryptographic engineering and key lifecycle.",
        domain="CYBERSECURITY",
        status="GENERATING_ASSETS",
        user_id=user.id,
    )
    db_session.add(course)
    db_session.flush()

    module = Module(
        course_id=course.id,
        title="Module 2: Applied Cryptography",
        sequence_order=1,
        description="Core concepts in cryptographic engineering.",
    )
    db_session.add(module)
    db_session.flush()

    lesson = Lesson(
        id=str(mock_assessment_lesson_data["lesson_id"]),
        module_id=module.id,
        title=mock_assessment_lesson_data["lesson_title"],
        sequence_order=1,
        estimated_minutes=20,
        learning_objectives=mock_assessment_lesson_data["learning_objectives"],
        target_concept_ids=[str(c.concept_id) for c in mock_assessment_lesson_data["concepts"]],
        source_chunk_ids=[str(ch.chunk_id) for ch in mock_assessment_lesson_data["chunks"]],
    )
    db_session.add(lesson)
    db_session.commit()

    return lesson
