"""
Integration tests for ContentExtractionPipeline and ExtractionPersistenceService
WBS 3.2 - Step 5: End-to-End Pipeline & Relational Persistence
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
from AI_Modules.Extraction.persistence import ExtractionPersistenceService
from AI_Modules.Extraction.tests.test_extractor import make_test_pdf, SAMPLE_TEXT_PAGE_1, SAMPLE_TEXT_PAGE_2


@pytest.fixture
def db_session():
    """In-memory SQLite database migrated with Alembic schema."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    config = Config(str(Path(__file__).resolve().parents[3] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    with Session(engine) as session:
        yield session


def test_pipeline_end_to_end_and_persistence(db_session: Session):
    # 1. Seed user, course, and document records
    user = User(email="member2@eduvance.ai", password_hash="hash", full_name="Member 2")
    db_session.add(user)
    db_session.flush()

    course = Course(user_id=user.id, title="Cybersecurity Foundations", domain="Security")
    db_session.add(course)
    db_session.flush()

    pdf_bytes = make_test_pdf([SAMPLE_TEXT_PAGE_1, SAMPLE_TEXT_PAGE_2])

    document = Document(
        course_id=course.id,
        filename="nist_guide.pdf",
        file_path="uploads/source.pdf",
        file_hash_sha256="dummyhash",
        page_count=2,
        file_size_bytes=len(pdf_bytes),
        upload_status="UPLOADED",
    )
    db_session.add(document)
    db_session.commit()

    # 2. Run the unified Content Extraction Pipeline
    pipeline = ContentExtractionPipeline()
    output = pipeline.process_course_documents(
        course_id=course.id,
        documents=[(document.id, pdf_bytes)],
        session=db_session,
        persist=True,
    )

    # 3. Verify Contract 1 conformance
    assert str(output.course_id) == str(course.id)
    assert len(output.chunks) >= 1
    assert len(output.concepts) >= 1

    # Verify chunks have page numbers and originating document ID
    for chunk in output.chunks:
        assert str(chunk.document_id) == str(document.id)
        assert chunk.page_number in (1, 2)
        assert len(chunk.text_content) >= 50

    # 4. Verify Database Persistence in relational tables
    persisted_chunks = db_session.scalars(
        select(ContentChunk).where(ContentChunk.document_id == str(document.id))
    ).all()
    assert len(persisted_chunks) == len(output.chunks)

    persisted_concepts = db_session.scalars(
        select(Concept).where(Concept.course_id == str(course.id))
    ).all()
    assert len(persisted_concepts) == len(output.concepts)

    # Verify statuses updated
    reloaded_doc = db_session.scalar(select(Document).where(Document.id == str(document.id)))
    assert reloaded_doc.upload_status == "EXTRACTED"

    reloaded_course = db_session.scalar(select(Course).where(Course.id == str(course.id)))
    assert reloaded_course.status == "EXTRACTED"

    # 5. Verify round-trip loading
    persistence_service = ExtractionPersistenceService()
    reloaded_output = persistence_service.load_extraction_output(db_session, course.id)
    assert reloaded_output is not None
    assert str(reloaded_output.course_id) == str(course.id)
    assert len(reloaded_output.chunks) == len(output.chunks)
    assert len(reloaded_output.concepts) == len(output.concepts)

