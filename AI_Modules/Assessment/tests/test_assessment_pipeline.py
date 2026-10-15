"""
Eduvance AI - Assessment Pipeline & Persistence Integration Tests
WBS 3.5 - Assessment Agent Testing

Tests:
- End-to-end integration: Quiz -> PracticalExercise -> DB Persistence.
- Database persistence into Quiz, QuizQuestion, and PracticalExercise tables.
- Idempotent re-generation without unique constraint violations.
- Foreign key linking between Lesson, Concepts, and Content Chunks.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from sqlalchemy.orm import Session

from AI_Modules.Assessment.pipeline import AssessmentGenerationPipeline
from AI_Modules.Assessment.schemas import AssessmentPackageOutput
from Database.models.all_models import Lesson, PracticalExercise, Quiz, QuizQuestion


def test_assessment_pipeline_end_to_end_persists_to_database(
    db_session: Session,
    persisted_db_lesson: Lesson,
    mock_assessment_lesson_data: dict,
):
    """Verifies complete assessment pipeline creates quizzes, questions, and exercises in DB."""
    pipeline = AssessmentGenerationPipeline()

    package = pipeline.process_lesson_assessment(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        learning_objectives=mock_assessment_lesson_data["learning_objectives"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        session=db_session,
        persist=True,
    )

    assert isinstance(package, AssessmentPackageOutput)

    str_lesson_id = str(mock_assessment_lesson_data["lesson_id"])

    # 1. Verify Quiz entity in database
    db_quiz = db_session.query(Quiz).filter(Quiz.lesson_id == str_lesson_id).first()
    assert db_quiz is not None
    assert db_quiz.passing_score == 70

    # 2. Verify QuizQuestion entities in database
    db_questions = (
        db_session.query(QuizQuestion)
        .filter(QuizQuestion.quiz_id == db_quiz.id)
        .order_by(QuizQuestion.sequence_order)
        .all()
    )
    assert len(db_questions) == len(package.quiz.questions)

    for idx, db_q in enumerate(db_questions, start=1):
        expected_q = package.quiz.questions[idx - 1]
        assert db_q.sequence_order == idx
        assert db_q.question_text == expected_q.question_text
        assert db_q.correct_answer == expected_q.correct_answer
        assert len(db_q.options) == len(expected_q.options)
        assert db_q.explanation == expected_q.explanation
        assert db_q.source_chunk_id == str(expected_q.source_chunk_id)

    # 3. Verify PracticalExercise entity in database
    db_exercise = db_session.query(PracticalExercise).filter(PracticalExercise.lesson_id == str_lesson_id).first()
    assert db_exercise is not None
    assert db_exercise.prompt == package.practical_exercise.prompt
    assert db_exercise.deliverable_description == package.practical_exercise.deliverable_description
    assert len(db_exercise.rubric_criteria) == len(package.practical_exercise.rubric_criteria)


def test_idempotent_regeneration_clears_old_records(
    db_session: Session,
    persisted_db_lesson: Lesson,
    mock_assessment_lesson_data: dict,
):
    """Verifies that re-running assessment generation replaces previous records cleanly."""
    pipeline = AssessmentGenerationPipeline()

    # First run (4 questions)
    pipeline.process_lesson_assessment(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        learning_objectives=mock_assessment_lesson_data["learning_objectives"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        num_questions=4,
        session=db_session,
        persist=True,
    )

    str_lesson_id = str(mock_assessment_lesson_data["lesson_id"])
    db_quiz = db_session.query(Quiz).filter(Quiz.lesson_id == str_lesson_id).first()
    first_quiz_id = db_quiz.id
    q_count_first = db_session.query(QuizQuestion).filter(QuizQuestion.quiz_id == first_quiz_id).count()
    assert q_count_first == 4

    # Second run (6 questions)
    pipeline.process_lesson_assessment(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        learning_objectives=mock_assessment_lesson_data["learning_objectives"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        num_questions=6,
        session=db_session,
        persist=True,
    )

    # Must still have exactly 1 quiz for this lesson
    quizzes = db_session.query(Quiz).filter(Quiz.lesson_id == str_lesson_id).all()
    assert len(quizzes) == 1
    new_quiz_id = quizzes[0].id

    # Must have exactly 6 questions
    q_count_second = db_session.query(QuizQuestion).filter(QuizQuestion.quiz_id == new_quiz_id).count()
    assert q_count_second == 6
