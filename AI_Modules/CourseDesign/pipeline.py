"""
Eduvance AI - Course Design Pipeline Orchestrator (Course Designer Agent)
WBS 3.3 - End-to-End Course Design Pipeline

Orchestrates the Course Designer workflow:
1. Ingests ContentExtractionOutput from WBS 3.2.
2. Updates course status to DESIGNING_COURSE.
3. Synthesizes modules, lessons, and Bloom's objectives via CourseDesigner.
4. Persists curriculum entities to database and transitions status to PENDING_APPROVAL.

Fulfills WBS 2.1 Contract 2 (CourseDesignOutput).

Owner: Member 2 (Content and RAG Engineer)
"""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from AI_Modules.Extraction.schemas import ContentExtractionOutput
from Database.models.all_models import Course
from .course_designer import CourseDesigner
from .persistence import CourseDesignPersistenceService
from .schemas import CourseDesignOutput


class CourseDesignPipeline:
    """
    High-level orchestrator for the Course Designer Agent lifecycle.
    """

    def __init__(
        self,
        designer: Optional[CourseDesigner] = None,
        persistence_service: Optional[CourseDesignPersistenceService] = None,
    ):
        self.designer = designer or CourseDesigner()
        self.persistence_service = persistence_service or CourseDesignPersistenceService()

    def process_course_curriculum(
        self,
        extraction_output: ContentExtractionOutput,
        session: Optional[Session] = None,
        persist: bool = True,
        course_title_override: Optional[str] = None,
        course_description_override: Optional[str] = None,
    ) -> CourseDesignOutput:
        """
        Executes end-to-end curriculum generation from extracted content.

        Args:
            extraction_output: Output from WBS 3.2 containing validated chunks and concepts.
            session: Optional active SQLAlchemy session.
            persist: Whether to commit modules and lessons to database.
            course_title_override: Optional user-specified title.
            course_description_override: Optional user-specified description.

        Returns:
            CourseDesignOutput conforming strictly to Contract 2.
        """
        course_id = extraction_output.course_id

        # Update initial state to DESIGNING_COURSE if session is active
        if session is not None and persist:
            course = session.query(Course).filter(Course.id == str(course_id)).first()
            if course:
                course.status = "DESIGNING_COURSE"
                session.flush()

        # Generate structured curriculum
        design_output = self.designer.generate_curriculum(
            extraction_output=extraction_output,
            course_title_override=course_title_override,
            course_description_override=course_description_override,
        )

        # Persist entities and transition status to PENDING_APPROVAL
        if session is not None and persist:
            self.persistence_service.persist_course_design(
                session=session,
                course_id=course_id,
                design=design_output,
            )

        return design_output
