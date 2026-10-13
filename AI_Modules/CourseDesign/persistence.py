"""
Eduvance AI - Course Design Database Persistence Service
WBS 3.3 - Course Entity Persistence & Instructor Review Workflows

Persists generated curriculum structures (Module, Lesson) into the relational
database, manages course status transitions, and supports instructor modifications
prior to final course approval.

Owner: Member 2 (Content and RAG Engineer)
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from Database.models.all_models import Course, Lesson, Module
from .schemas import CourseDesignOutput, LessonDesign, LessonUpdate, ModuleDesign, ModuleUpdate


class CourseDesignPersistenceService:
    """
    Manages database transactions for course design entities, status lifecycles,
    and instructor editing interactions.
    """

    def persist_course_design(
        self,
        session: Session,
        course_id: UUID,
        design: CourseDesignOutput,
        update_course_metadata: bool = True,
    ) -> List[Module]:
        """
        Persists a complete CourseDesignOutput into the database:
        1. Verifies parent Course exists.
        2. Clears any existing draft modules/lessons (if re-generating).
        3. Creates Module and Lesson records with sequence orders and JSON arrays.
        4. Transitions Course status to PENDING_APPROVAL.

        Returns:
            List of created SQLAlchemy Module model instances.
        """
        str_course_id = str(course_id)
        course = session.query(Course).filter(Course.id == str_course_id).first()
        if not course:
            raise ValueError(f"Course with ID '{course_id}' does not exist.")

        # Update course metadata if requested
        if update_course_metadata:
            course.title = design.course_title
            course.description = design.description

        # Remove existing modules/lessons if re-generating
        session.query(Module).filter(Module.course_id == str_course_id).delete(synchronize_session="fetch")
        session.flush()

        persisted_modules: List[Module] = []

        for mod_design in design.modules:
            db_module = Module(
                course_id=str_course_id,
                title=mod_design.title,
                sequence_order=mod_design.module_sequence,
                description=mod_design.description,
            )
            session.add(db_module)
            session.flush()  # Generates db_module.id

            for les_design in mod_design.lessons:
                db_lesson = Lesson(
                    module_id=db_module.id,
                    title=les_design.title,
                    sequence_order=les_design.lesson_sequence,
                    estimated_minutes=les_design.estimated_minutes,
                    learning_objectives=les_design.learning_objectives,
                    target_concept_ids=[str(cid) for cid in les_design.target_concept_ids],
                    source_chunk_ids=[str(cid) for cid in les_design.source_chunk_ids],
                )
                session.add(db_lesson)

            persisted_modules.append(db_module)

        # Transition status to PENDING_APPROVAL awaiting instructor review
        course.status = "PENDING_APPROVAL"
        session.commit()

        return persisted_modules

    def update_lesson(
        self,
        session: Session,
        lesson_id: str,
        update_data: LessonUpdate,
    ) -> Lesson:
        """Applies instructor edits to an individual lesson."""
        lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
        if not lesson:
            raise ValueError(f"Lesson with ID '{lesson_id}' not found.")

        if update_data.title is not None:
            lesson.title = update_data.title
        if update_data.estimated_minutes is not None:
            lesson.estimated_minutes = update_data.estimated_minutes
        if update_data.learning_objectives is not None:
            lesson.learning_objectives = update_data.learning_objectives
        if update_data.target_concept_ids is not None:
            lesson.target_concept_ids = [str(cid) for cid in update_data.target_concept_ids]
        if update_data.source_chunk_ids is not None:
            lesson.source_chunk_ids = [str(cid) for cid in update_data.source_chunk_ids]

        session.commit()
        session.refresh(lesson)
        return lesson

    def update_module(
        self,
        session: Session,
        module_id: str,
        update_data: ModuleUpdate,
    ) -> Module:
        """Applies instructor edits to a module."""
        module = session.query(Module).filter(Module.id == module_id).first()
        if not module:
            raise ValueError(f"Module with ID '{module_id}' not found.")

        if update_data.title is not None:
            module.title = update_data.title
        if update_data.description is not None:
            module.description = update_data.description

        session.commit()
        session.refresh(module)
        return module

    def reorder_lessons(
        self,
        session: Session,
        module_id: str,
        ordered_lesson_ids: List[str],
    ) -> List[Lesson]:
        """Re-sequences lessons within a module according to instructor ordering."""
        lessons = session.query(Lesson).filter(Lesson.module_id == module_id).all()
        lesson_map = {les.id: les for les in lessons}

        for new_seq, les_id in enumerate(ordered_lesson_ids, start=1):
            if les_id in lesson_map:
                lesson_map[les_id].sequence_order = new_seq

        session.commit()
        return sorted(lessons, key=lambda l: l.sequence_order)

    def approve_course_design(self, session: Session, course_id: UUID) -> Course:
        """
        Instructor approves the generated curriculum outline.
        Transitions course status to GENERATING_ASSETS, unlocking downstream
        Video, Assessment, and RAG indexing agents.
        """
        str_course_id = str(course_id)
        course = session.query(Course).filter(Course.id == str_course_id).first()
        if not course:
            raise ValueError(f"Course with ID '{course_id}' not found.")

        if course.status != "PENDING_APPROVAL":
            raise ValueError(
                f"Course cannot be approved: Current status is '{course.status}', "
                f"expected 'PENDING_APPROVAL'."
            )

        course.status = "GENERATING_ASSETS"
        session.commit()
        session.refresh(course)
        return course
