"""
Eduvance AI - Unified Content Extraction Pipeline (Content Agent)
WBS 3.2 - Step 5: Pipeline Orchestrator

Integrates:
1. Document validation (PDFValidator)
2. Page-by-page text extraction (TextExtractor)
3. Token-aware chunking (DocumentChunker)
4. Domain concept extraction & prerequisite graph (ConceptExtractor)
5. Database persistence (ExtractionPersistenceService)

Fulfills WBS 2.1 Contract 1 (ContentExtractionOutput).

Owner: Member 2 (Content and RAG Engineer)
"""

from pathlib import Path
from typing import List, Optional, Tuple, Union, BinaryIO
from uuid import UUID

from sqlalchemy.orm import Session

from .chunker import DocumentChunker
from .concept_extractor import ConceptExtractor
from .pdf_validator import PDFValidator
from .persistence import ExtractionPersistenceService
from .schemas import ContentExtractionOutput, ExtractedChunk, ExtractedConcept
from .text_extractor import TextExtractor


class ContentExtractionPipeline:
    """
    Orchestrates end-to-end content processing for uploaded training documents
    into structured, source-grounded chunks and concepts.
    """

    def __init__(
        self,
        validator: Optional[PDFValidator] = None,
        extractor: Optional[TextExtractor] = None,
        chunker: Optional[DocumentChunker] = None,
        concept_extractor: Optional[ConceptExtractor] = None,
        persistence_service: Optional[ExtractionPersistenceService] = None,
    ):
        self.validator = validator or PDFValidator()
        self.extractor = extractor or TextExtractor(validator=self.validator)
        self.chunker = chunker or DocumentChunker()
        self.concept_extractor = concept_extractor or ConceptExtractor()
        self.persistence_service = persistence_service or ExtractionPersistenceService()

    def process_course_documents(
        self,
        course_id: UUID,
        documents: List[Tuple[UUID, Union[str, Path, bytes, BinaryIO]]],
        session: Optional[Session] = None,
        persist: bool = True,
    ) -> ContentExtractionOutput:
        """
        Executes the extraction pipeline across one or more documents for a given course.

        Args:
            course_id: UUID of the course container.
            documents: List of tuples (document_id, document_source_path_or_bytes).
            session: Optional SQLAlchemy session for database persistence.
            persist: Whether to commit output to the database if session is provided.

        Returns:
            ContentExtractionOutput conforming to WBS 2.1 Contract 1.
        """
        if not documents:
            raise ValueError("At least one source document is required for extraction.")

        all_chunks: List[ExtractedChunk] = []

        # 1. Process each document into validated, source-anchored chunks
        for doc_id, doc_source in documents:
            # Extract cleaned pages
            pages = self.extractor.extract_pages(doc_source)

            # Chunk document pages
            doc_chunks = self.chunker.chunk_pages(pages, document_id=doc_id)
            all_chunks.extend(doc_chunks)

        if not all_chunks:
            raise ValueError("No valid content chunks could be extracted from provided documents.")

        # Re-index global chunks if multi-document to preserve sequence
        for idx, chunk in enumerate(all_chunks):
            chunk.chunk_index = idx

        # 2. Extract domain concepts and prerequisite links across the accumulated chunks
        concepts: List[ExtractedConcept] = self.concept_extractor.extract_concepts(all_chunks)

        # 3. Assemble validated Contract 1 output
        output = ContentExtractionOutput(
            course_id=course_id,
            chunks=all_chunks,
            concepts=concepts,
        )

        # 4. Optional Database Persistence
        if session is not None and persist:
            self.persistence_service.save_extraction_output(session, output, commit=True)

        return output
