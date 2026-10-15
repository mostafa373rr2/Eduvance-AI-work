"""
Eduvance AI - Quiz Evaluator Tests
WBS 3.5 - Deterministic Assessment Grading & Diagnostic Feedback

Tests:
- Deterministic submission scoring and percentage calculations.
- Pass/fail determination against the 70% threshold.
- Concept mastery tracking (mastered vs revision recommended).
- Explainable feedback messaging for remedial learning.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from AI_Modules.Assessment.evaluator import QuizEvaluator
from AI_Modules.Assessment.quiz_generator import QuizGenerator
from AI_Modules.Assessment.schemas import QuizResult, QuizSubmission


def test_evaluator_perfect_score(mock_assessment_lesson_data):
    """Learner who answers 100% correctly passes with all concepts mastered."""
    generator = QuizGenerator()
    quiz = generator.generate_quiz(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        num_questions=5,
    )

    # Build 100% correct submission
    answers = {q.question_number: q.correct_answer for q in quiz.questions}
    submission = QuizSubmission(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        answers=answers,
    )

    evaluator = QuizEvaluator()
    result = evaluator.evaluate_submission(quiz, submission)

    assert isinstance(result, QuizResult)
    assert result.score_percentage == 100.0
    assert result.correct_count == 5
    assert result.passed is True
    assert len(result.revision_recommended_concept_ids) == 0
    assert "Congratulations" in result.recommendation_message


def test_evaluator_failing_score_triggers_revision(mock_assessment_lesson_data):
    """Learner who scores below 70% receives revision recommendations."""
    generator = QuizGenerator()
    quiz = generator.generate_quiz(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        num_questions=5,
    )

    # Only answer Q1 correctly; answer all others incorrectly
    answers = {
        1: quiz.questions[0].correct_answer,
        2: "Incorrect Answer Option",
        3: "Incorrect Answer Option",
        4: "Incorrect Answer Option",
        5: "Incorrect Answer Option",
    }
    submission = QuizSubmission(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        answers=answers,
    )

    evaluator = QuizEvaluator()
    result = evaluator.evaluate_submission(quiz, submission)

    # 1 out of 5 = 20.0% (< 70% passing threshold)
    assert result.score_percentage == 20.0
    assert result.correct_count == 1
    assert result.passed is False
    assert len(result.revision_recommended_concept_ids) >= 1
    assert "Revision is recommended" in result.recommendation_message


def test_evaluator_missing_answers_treated_as_incorrect(mock_assessment_lesson_data):
    """Unanswered questions count as incorrect."""
    generator = QuizGenerator()
    quiz = generator.generate_quiz(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        num_questions=4,
    )

    # Submit empty answers dict
    submission = QuizSubmission(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        answers={},
    )

    evaluator = QuizEvaluator()
    result = evaluator.evaluate_submission(quiz, submission)

    assert result.correct_count == 0
    assert result.score_percentage == 0.0
    assert result.passed is False
