"""
Eduvance AI - Content Extraction Persistence Layer
WBS 3.2 - Step 5: Database Persistence Service

Persists ContentExtractionOutput into SQLAlchemy 2.0 tables:
- content_chunks (ContentChunk)
- concepts (Concept)
- Updates Document.upload_status -> "EXTRACTED"
- Updates Course.status -> "EXTRACTED"

Owner: Member 2 (Content and RAG Engineer)
"""

from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from Database.models.all_models import Concept, ContentChunk, Course, Document
from .schemas import ContentExtractionOutput, DifficultyLevel, ExtractedChunk, ExtractedConcept


class ExtractionPersistenceService:
    """Handles database persistence and loading for Content Agent extraction outputs."""

    def save_extraction_output(
        self,
        session: Session,
        extraction: ContentExtractionOutput,
        commit: bool = True,
    ) -> None:
        """
        Persists extracted chunks and domain concepts into the database within a transaction.
        Updates document upload statuses and the parent course status.
        """
        course_id_str = str(extraction.course_id)

        # 1. Save Content Chunks
        chunk_id_map: Dict[str, ContentChunk] = {}
        for chunk in extraction.chunks:
            chunk_orm = ContentChunk(
                id=str(chunk.chunk_id),
                document_id=str(chunk.document_id),
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                text_content=chunk.text_content,
                token_count=chunk.token_count,
                metadata_json={"section_header": chunk.section_header} if chunk.section_header else {},
            )
            session.add(chunk_orm)
            chunk_id_map[str(chunk.chunk_id)] = chunk_orm

        session.flush()

        # 2. Build name-to-UUID map for concept prerequisite resolution
        concept_name_to_id: Dict[str, str] = {c.name: str(c.concept_id) for c in extraction.concepts}

        # 3. Save Concepts
        for concept in extraction.concepts:
            # Map prerequisite names to resolved concept IDs
            resolved_prereq_ids = [
                concept_name_to_id[p_name]
                for p_name in concept.prerequisite_names
                if p_name in concept_name_to_id
            ]

            concept_orm = Concept(
                id=str(concept.concept_id),
                course_id=course_id_str,
                name=concept.name,
                description=concept.description,
                difficulty=concept.difficulty.value if hasattr(concept.difficulty, "value") else str(concept.difficulty),
                prerequisite_concept_ids=resolved_prereq_ids,
                source_chunk_ids=[str(cid) for cid in concept.source_chunk_ids],
            )
            session.add(concept_orm)

        # 4. Update Document upload_status for affected documents
        unique_doc_ids = {str(chunk.document_id) for chunk in extraction.chunks}
        for doc_id_str in unique_doc_ids:
            doc = session.scalar(select(Document).where(Document.id == doc_id_str))
            if doc:
                doc.upload_status = "EXTRACTED"

        # 5. Update Course status to EXTRACTED
        course = session.scalar(select(Course).where(Course.id == course_id_str))
        if course:
            course.status = "EXTRACTED"

        if commit:
            session.commit()
        else:
            session.flush()

    def load_extraction_output(
        self,
        session: Session,
        course_id: UUID,
    ) -> Optional[ContentExtractionOutput]:
        """Loads and reconstructs a ContentExtractionOutput schema from the database."""
        course_id_str = str(course_id)

        # Query all documents for this course
        docs = session.scalars(select(Document).where(Document.course_id == course_id_str)).all()
        if not docs:
            return None

        doc_ids = [d.id for d in docs]
        chunks_orm = session.scalars(
            select(ContentChunk)
            .where(ContentChunk.document_id.in_(doc_ids))
            .order_by(ContentChunk.document_id, ContentChunk.chunk_index)
        ).all()

        concepts_orm = session.scalars(
            select(Concept).where(Concept.course_id == course_id_str)
        ).all()

        if not chunks_orm or not concepts_orm:
            return None

        # Map concepts by ID to resolve prerequisite names
        id_to_name: Dict[str, str] = {c.id: c.name for c in concepts_orm}

        chunks: List[ExtractedChunk] = [
            ExtractedChunk(
                chunk_id=UUID(c.id),
                document_id=UUID(c.document_id),
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                text_content=c.text_content,
                token_count=c.token_count,
                section_header=c.metadata_json.get("section_header") if c.metadata_json else None,
            )
            for c in chunks_orm
        ]

        concepts: List[ExtractedConcept] = [
            ExtractedConcept(
                concept_id=UUID(c.id),
                name=c.name,
                description=c.description,
                difficulty=DifficultyLevel(c.difficulty) if c.difficulty in DifficultyLevel._value2member_map_ else DifficultyLevel.BEGINNER,
                prerequisite_names=[id_to_name[pid] for pid in (c.prerequisite_concept_ids or []) if pid in id_to_name],
                source_chunk_ids=[UUID(cid) for cid in (c.source_chunk_ids or [])],
            )
            for c in concepts_orm
        ]

        return ContentExtractionOutput(
            course_id=course_id,
            chunks=chunks,
            concepts=concepts,
        )
