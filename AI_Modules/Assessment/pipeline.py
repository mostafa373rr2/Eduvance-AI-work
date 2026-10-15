"""
Eduvance AI - Assessment Generation Pipeline Orchestrator (Assessment Agent)
WBS 3.5 - End-to-End Assessment Package Generation

Coordinates:
1. Concept and chunk grounded quiz generation (QuizGenerator -> Contract 5)
2. Practical assignment & rubric generation (PracticalExerciseGenerator -> Contract 5)
3. Relational database persistence (AssessmentPersistenceService)

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from AI_Modules.Extraction.schemas import ExtractedChunk, ExtractedConcept
from .exercise_generator import PracticalExerciseGenerator
from .persistence import AssessmentPersistenceService
from .quiz_generator import QuizGenerator
from .schemas import AssessmentPackageOutput, PracticalExerciseSpec, QuizSpec


class AssessmentGenerationPipeline:
    """
    Master coordinator for the Assessment Agent workflow.
    """

    def __init__(
        self,
        quiz_generator: Optional[QuizGenerator] = None,
        exercise_generator: Optional[PracticalExerciseGenerator] = None,
        persistence_service: Optional[AssessmentPersistenceService] = None,
    ):
        self.quiz_generator = quiz_generator or QuizGenerator()
        self.exercise_generator = exercise_generator or PracticalExerciseGenerator()
        self.persistence_service = persistence_service or AssessmentPersistenceService()

    def process_lesson_assessment(
        self,
        lesson_id: UUID,
        lesson_title: str,
        learning_objectives: List[str],
        concepts: List[Union[ExtractedConcept, Dict[str, Any]]],
        chunks: List[Union[ExtractedChunk, Dict[str, Any]]],
        num_questions: Optional[int] = None,
        passing_score: Optional[int] = None,
        session: Optional[Session] = None,
        persist: bool = True,
    ) -> AssessmentPackageOutput:
        """
        Executes end-to-end assessment synthesis and database persistence for a lesson.
        """
        # 1. Generate grounded QuizSpec (Contract 5)
        quiz_spec: QuizSpec = self.quiz_generator.generate_quiz(
            lesson_id=lesson_id,
            lesson_title=lesson_title,
            concepts=concepts,
            chunks=chunks,
            num_questions=num_questions,
            passing_score=passing_score,
        )

        # 2. Generate applied PracticalExerciseSpec (Contract 5)
        exercise_spec: PracticalExerciseSpec = self.exercise_generator.generate_exercise(
            lesson_id=lesson_id,
            lesson_title=lesson_title,
            learning_objectives=learning_objectives,
            concepts=concepts,
            chunks=chunks,
        )

        # 3. Assemble validated AssessmentPackageOutput (Root Contract 5)
        assessment_package = AssessmentPackageOutput(
            lesson_id=lesson_id,
            quiz=quiz_spec,
            practical_exercise=exercise_spec,
        )

        # 4. Database persistence
        if session is not None and persist:
            self.persistence_service.persist_assessment_package(
                session=session,
                package=assessment_package,
            )

        return assessment_package
