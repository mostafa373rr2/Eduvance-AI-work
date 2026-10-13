"""
Eduvance AI - Course Design Test Fixtures
WBS 3.3 - Course Designer Agent Testing

Provides standard fixtures for testing course generation:
- Synthetic ContentExtractionOutput adhering to Contract 1.
- In-memory SQLite SQLAlchemy session with User, Course, and Document records.

Owner: Member 2 (Content and RAG Engineer)
"""

from typing import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from AI_Modules.Extraction.schemas import (
    ContentExtractionOutput,
    DifficultyLevel,
    ExtractedChunk,
    ExtractedConcept,
)
from Database.models.all_models import Base, Course, Document, User


@pytest.fixture
def mock_extraction_output() -> ContentExtractionOutput:
    """Provides a realistic ContentExtractionOutput (Contract 1) with 6 concepts and 8 chunks."""
    course_id = uuid4()
    doc_id = uuid4()

    # Generate 8 source chunks with varying section headers and page anchors
    chunks = [
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=0,
            page_number=1,
            section_header="1. Introduction to Cybersecurity Governance",
            text_content=(
                "Cybersecurity governance establishes the foundational framework for managing risk "
                "across digital ecosystems. It defines roles, responsibilities, and accountability."
            ),
            token_count=120,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=1,
            page_number=2,
            section_header="1.1 Asset Management Fundamentals",
            text_content=(
                "Asset management enables organizations to achieve visibility into all data, software, "
                "hardware, and personnel assets. Complete inventorying is critical before securing access."
            ),
            token_count=135,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=2,
            page_number=3,
            section_header="2. Risk Assessment Methodologies",
            text_content=(
                "Risk assessment identifies vulnerabilities, potential threat vectors, and estimated impacts. "
                "Quantitative and qualitative scoring models prioritize mitigation resources."
            ),
            token_count=140,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=3,
            page_number=4,
            section_header="2.1 Identity and Access Management",
            text_content=(
                "Identity and access management controls authentication, least-privilege authorization, and "
                "credential rotation. Multi-factor authentication forms a foundational defensive layer."
            ),
            token_count=130,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=4,
            page_number=5,
            section_header="3. Incident Detection and Response",
            text_content=(
                "Incident detection monitors anomalous event logs and behavioral telemetry in real-time. "
                "Predefined response playbooks contain, isolate, and eradicate compromised assets."
            ),
            token_count=150,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=5,
            page_number=6,
            section_header="3.1 Disaster Recovery and Continuity",
            text_content=(
                "Business continuity ensures operational resilience following major system disruptions. "
                "Regular immutable backups and recovery point objectives (RPO) mitigate ransomware impacts."
            ),
            token_count=145,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=6,
            page_number=7,
            section_header="4. Continuous Monitoring and Auditing",
            text_content=(
                "Continuous compliance monitoring evaluates security controls against industry standards. "
                "Automated audit trails maintain tamper-evident historical verification for regulators."
            ),
            token_count=160,
        ),
        ExtractedChunk(
            chunk_id=uuid4(),
            document_id=doc_id,
            chunk_index=7,
            page_number=8,
            section_header="4.1 Adaptive Security Optimization",
            text_content=(
                "Adaptive security architectures continuously incorporate threat intelligence feedback loops. "
                "Post-incident reviews dynamically update defense postures against evolving adversary vectors."
            ),
            token_count=155,
        ),
    ]

    # Generate 6 domain concepts with clear prerequisite hierarchy
    concepts = [
        ExtractedConcept(
            concept_id=uuid4(),
            name="Cybersecurity Governance",
            description="Foundational accountability structures and risk management policies across organizations.",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisite_names=[],
            source_chunk_ids=[chunks[0].chunk_id],
        ),
        ExtractedConcept(
            concept_id=uuid4(),
            name="Asset Inventory Management",
            description="Comprehensive identification, classification, and tracking of enterprise hardware and software.",
            difficulty=DifficultyLevel.BEGINNER,
            prerequisite_names=["Cybersecurity Governance"],
            source_chunk_ids=[chunks[1].chunk_id],
        ),
        ExtractedConcept(
            concept_id=uuid4(),
            name="Quantitative Risk Assessment",
            description="Systematic calculation of vulnerability likelihood and organizational threat impact.",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisite_names=["Asset Inventory Management"],
            source_chunk_ids=[chunks[2].chunk_id],
        ),
        ExtractedConcept(
            concept_id=uuid4(),
            name="Identity & Access Governance",
            description="Principle of least privilege, multi-factor authentication, and centralized access directory.",
            difficulty=DifficultyLevel.INTERMEDIATE,
            prerequisite_names=["Cybersecurity Governance"],
            source_chunk_ids=[chunks[3].chunk_id],
        ),
        ExtractedConcept(
            concept_id=uuid4(),
            name="Incident Response & Telemetry",
            description="Real-time security operations center detection, containment procedures, and forensic analysis.",
            difficulty=DifficultyLevel.ADVANCED,
            prerequisite_names=["Identity & Access Governance", "Quantitative Risk Assessment"],
            source_chunk_ids=[chunks[4].chunk_id, chunks[5].chunk_id],
        ),
        ExtractedConcept(
            concept_id=uuid4(),
            name="Continuous Adaptive Auditing",
            description="Dynamic security metrics, compliance automation, and post-incident architectural refinement.",
            difficulty=DifficultyLevel.ADVANCED,
            prerequisite_names=["Incident Response & Telemetry"],
            source_chunk_ids=[chunks[6].chunk_id, chunks[7].chunk_id],
        ),
    ]

    return ContentExtractionOutput(
        course_id=course_id,
        chunks=chunks,
        concepts=concepts,
    )


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
def sample_persisted_course(db_session: Session, mock_extraction_output: ContentExtractionOutput) -> Course:
    """Creates and persists a sample User, Course, and Document in the DB session."""
    user = User(
        email="instructor@eduvance.ai",
        password_hash="test_bcrypt_hash",
        full_name="Dr. Jane Doe",
        role="INSTRUCTOR",
    )
    db_session.add(user)
    db_session.flush()

    course = Course(
        id=str(mock_extraction_output.course_id),
        user_id=user.id,
        title="Introduction to NIST Cybersecurity Framework",
        description="Comprehensive training course on foundational security governance.",
        domain="CYBERSECURITY",
        status="EXTRACTED",
    )
    db_session.add(course)
    db_session.flush()

    doc = Document(
        id=str(mock_extraction_output.chunks[0].document_id),
        course_id=course.id,
        filename="nist_csf_2.0.pdf",
        file_path="/storage/courses/nist_csf_2.0.pdf",
        file_hash_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        page_count=8,
        file_size_bytes=1048576,
        upload_status="EXTRACTED",
    )
    db_session.add(doc)
    db_session.commit()

    return course
