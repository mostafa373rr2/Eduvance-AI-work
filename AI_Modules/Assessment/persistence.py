"""
Eduvance AI - Assessment Database Persistence Service
WBS 3.5 - Relational Storage for Quizzes, Questions & Exercises

Commits generated AssessmentPackageOutput entities into the relational database
tables: quizzes, quiz_questions, and practical_exercises.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from typing import Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from Database.models.all_models import Lesson, PracticalExercise, Quiz, QuizQuestion
from .schemas import AssessmentPackageOutput


class AssessmentPersistenceService:
    """
    Manages database transactions for quiz questions and practical exercises.
    """

    def persist_assessment_package(
        self,
        session: Session,
        package: AssessmentPackageOutput,
    ) -> Tuple[Quiz, PracticalExercise]:
        """
        Persists a complete AssessmentPackageOutput into the database:
        1. Verifies parent Lesson exists.
        2. Clears previous quiz/exercise records if re-generating.
        3. Creates Quiz and QuizQuestion records.
        4. Creates PracticalExercise record.
        5. Commits transaction and returns created models.
        """
        str_lesson_id = str(package.lesson_id)
        lesson = session.query(Lesson).filter(Lesson.id == str_lesson_id).first()
        if not lesson:
            raise ValueError(f"Lesson with ID '{package.lesson_id}' does not exist in database.")

        # Remove existing quiz and practical exercises for this lesson if re-generating
        session.query(Quiz).filter(Quiz.lesson_id == str_lesson_id).delete(synchronize_session="fetch")
        session.query(PracticalExercise).filter(PracticalExercise.lesson_id == str_lesson_id).delete(synchronize_session="fetch")
        session.flush()

        # 1. Create Quiz
        db_quiz = Quiz(
            lesson_id=str_lesson_id,
            passing_score=package.quiz.passing_score_percentage,
        )
        session.add(db_quiz)
        session.flush()  # Populates db_quiz.id

        # 2. Create Quiz Questions
        for q_spec in package.quiz.questions:
            db_question = QuizQuestion(
                quiz_id=db_quiz.id,
                question_text=q_spec.question_text,
                question_type=q_spec.question_type.value,
                options=q_spec.options,
                correct_answer=q_spec.correct_answer,
                explanation=q_spec.explanation,
                target_concept_id=str(q_spec.target_concept_id) if q_spec.target_concept_id else None,
                source_chunk_id=str(q_spec.source_chunk_id) if q_spec.source_chunk_id else None,
                sequence_order=q_spec.question_number,
            )
            session.add(db_question)

        # 3. Create Practical Exercise
        db_exercise = PracticalExercise(
            lesson_id=str_lesson_id,
            prompt=package.practical_exercise.prompt,
            deliverable_description=package.practical_exercise.deliverable_description,
            starter_template=package.practical_exercise.starter_template,
            rubric_criteria=[c.model_dump() for c in package.practical_exercise.rubric_criteria],
        )
        session.add(db_exercise)

        session.commit()
        session.refresh(db_quiz)
        session.refresh(db_exercise)

        return db_quiz, db_exercise
