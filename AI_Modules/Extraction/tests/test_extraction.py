"""
Comprehensive Integration & Edge-Case Test Suite for Content Agent
WBS 3.2 - Step 6: Full Workflow Conformance & Boundary Verification
"""

from pathlib import Path
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from Database.models.all_models import Concept, ContentChunk, Course, Document, User
from AI_Modules.Extraction.pipeline import ContentExtractionPipeline
from AI_Modules.Extraction.schemas import ContentExtractionOutput
from AI_Modules.Extraction.tests.test_extractor import (
    make_test_pdf,
    SAMPLE_TEXT_PAGE_1,
    SAMPLE_TEXT_PAGE_2,
)


@pytest.fixture
def clean_db():
    """In-memory SQLite database instance with all Alembic migrations."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    with Session(engine) as session:
        yield session


def test_multi_document_processing(clean_db: Session):
    """Verifies that multiple documents (up to 3 files) for a course are ingested, chunked, and aggregated."""
    user = User(email="prof@eduvance.ai", password_hash="hash", full_name="Instructor")
    clean_db.add(user)
    clean_db.flush()

    course = Course(user_id=user.id, title="Enterprise Security Architecture", domain="Cybersecurity")
    clean_db.add(course)
    clean_db.flush()

    # Document 1: Core Framework
    doc1_bytes = make_test_pdf([
        (
            "Section 1. Identity & Access Management is defined as the business process ensuring authorized access "
            "to physical systems and digital services across enterprise environments."
        ),
        (
            "Section 2. Role-Based Access Control governs privilege management across directory services, "
            "enforcing least privilege and segregation of duties for security compliance."
        ),
    ])
    doc1 = Document(
        course_id=course.id,
        filename="doc1_iam.pdf",
        file_path="uploads/doc1.pdf",
        file_hash_sha256="hash1",
        page_count=2,
        file_size_bytes=len(doc1_bytes),
        upload_status="UPLOADED",
    )
    clean_db.add(doc1)

    # Document 2: Threat Detection
    doc2_bytes = make_test_pdf([
        (
            "Section 3. Incident Response refers to the coordinated protocol for containing and mitigating security breaches, "
            "incorporating forensic investigation and stakeholder remediation plans."
        ),
        (
            "Section 4. Continuous Threat Monitoring ensures real-time logging and anomalous telemetry analysis "
            "across operational cloud infrastructure and distributed endpoint nodes."
        ),
    ])
    doc2 = Document(
        course_id=course.id,
        filename="doc2_ir.pdf",
        file_path="uploads/doc2.pdf",
        file_hash_sha256="hash2",
        page_count=2,
        file_size_bytes=len(doc2_bytes),
        upload_status="UPLOADED",
    )

    clean_db.add(doc2)
    clean_db.commit()

    pipeline = ContentExtractionPipeline()
    output = pipeline.process_course_documents(
        course_id=course.id,
        documents=[(doc1.id, doc1_bytes), (doc2.id, doc2_bytes)],
        session=clean_db,
        persist=True,
    )

    # Verify combined chunks
    assert len(output.chunks) >= 2
    # Ensure sequential global indexing across documents
    for i, chunk in enumerate(output.chunks):
        assert chunk.chunk_index == i
        assert str(chunk.document_id) in {str(doc1.id), str(doc2.id)}


    # Verify concepts aggregate across both documents
    concept_names = [c.name for c in output.concepts]
    assert any("Identity" in name or "Access" in name for name in concept_names)
    assert any("Incident" in name or "Monitoring" in name for name in concept_names)

    # Verify database state
    db_chunks = clean_db.scalars(
        select(ContentChunk).where(ContentChunk.document_id.in_([doc1.id, doc2.id]))
    ).all()
    assert len(db_chunks) == len(output.chunks)

    # Both documents transitioned to EXTRACTED
    assert clean_db.scalar(select(Document).where(Document.id == doc1.id)).upload_status == "EXTRACTED"
    assert clean_db.scalar(select(Document).where(Document.id == doc2.id)).upload_status == "EXTRACTED"


def test_pipeline_traceability_guarantee():
    """Verifies that every chunk and concept has verifiable spatial page and chunk anchors."""
    doc_id = uuid4()
    course_id = uuid4()
    pdf_bytes = make_test_pdf([SAMPLE_TEXT_PAGE_1, SAMPLE_TEXT_PAGE_2])

    pipeline = ContentExtractionPipeline()
    output = pipeline.process_course_documents(
        course_id=course_id,
        documents=[(doc_id, pdf_bytes)],
        session=None,
        persist=False,
    )

    # Every chunk must trace to doc_id and a valid 1-indexed page
    valid_chunk_ids = set()
    for chunk in output.chunks:
        assert chunk.document_id == doc_id
        assert chunk.page_number in (1, 2)
        valid_chunk_ids.add(chunk.chunk_id)

    # Every concept must reference real chunk UUIDs
    for concept in output.concepts:
        assert len(concept.source_chunk_ids) > 0
        for src_id in concept.source_chunk_ids:
            assert src_id in valid_chunk_ids


def test_pipeline_rejects_empty_document_list():
    pipeline = ContentExtractionPipeline()
    with pytest.raises(ValueError, match="At least one source document is required"):
        pipeline.process_course_documents(course_id=uuid4(), documents=[])


def test_pipeline_rejects_scanned_pdf():
    pipeline = ContentExtractionPipeline()
    empty_pdf_bytes = make_test_pdf(["P1", "P2"])  # insufficient character density
    with pytest.raises(ValueError, match="PDF validation failed"):
        pipeline.process_course_documents(
            course_id=uuid4(),
            documents=[(uuid4(), empty_pdf_bytes)],
        )


def test_pipeline_determinism():
    """Running extraction twice on identical input produces identical chunk counts and concepts."""
    course_id = uuid4()
    doc_id = uuid4()
    pdf_bytes = make_test_pdf([SAMPLE_TEXT_PAGE_1, SAMPLE_TEXT_PAGE_2])

    pipeline = ContentExtractionPipeline()
    out1 = pipeline.process_course_documents(course_id, [(doc_id, pdf_bytes)])
    out2 = pipeline.process_course_documents(course_id, [(doc_id, pdf_bytes)])

    assert len(out1.chunks) == len(out2.chunks)
    assert len(out1.concepts) == len(out2.concepts)
    assert [c.name for c in out1.concepts] == [c.name for c in out2.concepts]
    assert [ch.text_content for ch in out1.chunks] == [ch.text_content for ch in out2.chunks]
