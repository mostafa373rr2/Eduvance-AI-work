"""
Eduvance AI - Quiz Generator Tests
WBS 3.5 - Automated Assessment Synthesis

Tests:
- Generation of Contract 5 compliant QuizSpec objects.
- Correct answer membership within options list.
- Balanced question types (MCQ and TRUE_FALSE).
- Target concept and source chunk provenance guarantees.
- Bounded question count scaling [4, 8].

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

import pytest

from AI_Modules.Assessment.quiz_generator import QuizGenerator
from AI_Modules.Assessment.schemas import QuestionType, QuizSpec


def test_generate_quiz_satisfies_contract_5(mock_assessment_lesson_data):
    """Verifies generated quiz satisfies all Contract 5 constraints."""
    generator = QuizGenerator()
    quiz = generator.generate_quiz(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
    )

    assert isinstance(quiz, QuizSpec)
    assert 4 <= len(quiz.questions) <= 8
    assert quiz.passing_score_percentage == 70

    valid_chunk_ids = {c.chunk_id for c in mock_assessment_lesson_data["chunks"]}
    valid_concept_ids = {c.concept_id for c in mock_assessment_lesson_data["concepts"]}

    has_mcq = False
    has_tf = False

    for idx, q in enumerate(quiz.questions, start=1):
        assert q.question_number == idx
        assert q.correct_answer in q.options
        assert len(q.explanation) >= 10
        assert q.source_chunk_id in valid_chunk_ids
        assert q.target_concept_id in valid_concept_ids or q.target_concept_id in valid_chunk_ids

        if q.question_type == QuestionType.MCQ:
            has_mcq = True
            assert len(q.options) == 4
        elif q.question_type == QuestionType.TRUE_FALSE:
            has_tf = True
            assert q.options == ["True", "False"]

    # Verify diversity of question types
    assert has_mcq
    assert has_tf


def test_custom_question_count_clamping(mock_assessment_lesson_data):
    """Verifies question count is clamped within [4, 8]."""
    generator = QuizGenerator()

    # Request 6 questions
    q6 = generator.generate_quiz(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        num_questions=6,
    )
    assert len(q6.questions) == 6

    # Request 12 questions (clamps to max 8)
    q8 = generator.generate_quiz(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        num_questions=12,
    )
    assert len(q8.questions) == 8

    # Request 1 question (clamps to min 4)
    q4 = generator.generate_quiz(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
        num_questions=1,
    )
    assert len(q4.questions) == 4


def test_quiz_generator_rejects_empty_chunks(mock_assessment_lesson_data):
    """Verifies generator raises ValueError when chunks are omitted."""
    generator = QuizGenerator()
    with pytest.raises(ValueError) as exc_info:
        generator.generate_quiz(
            lesson_id=mock_assessment_lesson_data["lesson_id"],
            lesson_title=mock_assessment_lesson_data["lesson_title"],
            concepts=mock_assessment_lesson_data["concepts"],
            chunks=[],
        )
    assert "source chunks" in str(exc_info.value)
