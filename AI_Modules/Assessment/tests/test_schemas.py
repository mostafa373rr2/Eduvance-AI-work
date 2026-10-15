"""
Eduvance AI - Assessment Schema Conformance Tests
WBS 3.5 - Step 1 Test Suite: Contract 5 Verification

Tests strict validation constraints of:
- QuizQuestionSpec (options [2, 4], correct answer membership, True/False format)
- QuizSpec (questions [4, 8], passing score [50, 100])
- PracticalExerciseSpec (rubric criteria >= 2, prompt length)
- AssessmentPackageOutput (Root Contract 5)

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from uuid import uuid4
import pytest
from pydantic import ValidationError

from AI_Modules.Assessment.schemas import (
    AssessmentPackageOutput,
    PracticalExerciseSpec,
    QuestionType,
    QuizQuestionSpec,
    QuizSpec,
    RubricCriterionSpec,
)


def test_quiz_question_spec_valid():
    """Valid MCQ and TRUE_FALSE questions satisfy Contract 5 schema."""
    mcq = QuizQuestionSpec(
        question_number=1,
        question_type=QuestionType.MCQ,
        question_text="What is the primary function of an HSM in cryptographic key management?",
        options=[
            "Tamper-resistant key generation and storage.",
            "Dynamic web page styling and rendering.",
            "Local file compression algorithm.",
            "Unrestricted public directory sharing.",
        ],
        correct_answer="Tamper-resistant key generation and storage.",
        explanation="HSMs provide dedicated hardware isolation to protect cryptographic keys.",
        target_concept_id=uuid4(),
        source_chunk_id=uuid4(),
    )
    assert mcq.question_number == 1
    assert mcq.correct_answer in mcq.options

    tf = QuizQuestionSpec(
        question_number=2,
        question_type=QuestionType.TRUE_FALSE,
        question_text="Automated key rotation bounds cryptanalytic exposure over time.",
        options=["True", "False"],
        correct_answer="True",
        explanation="Rotating keys limits the total volume of ciphertext encrypted under a single key.",
        target_concept_id=uuid4(),
        source_chunk_id=uuid4(),
    )
    assert tf.question_type == QuestionType.TRUE_FALSE
    assert len(tf.options) == 2


def test_quiz_question_correct_answer_must_be_in_options():
    """correct_answer must be present in options list."""
    with pytest.raises(ValidationError) as exc_info:
        QuizQuestionSpec(
            question_number=1,
            question_type=QuestionType.MCQ,
            question_text="Which algorithm is asymmetric?",
            options=["AES", "DES", "ChaCha20", "Blowfish"],
            correct_answer="RSA",  # Not in options
            explanation="RSA is asymmetric.",
            target_concept_id=uuid4(),
            source_chunk_id=uuid4(),
        )
    assert "correct_answer" in str(exc_info.value)


def test_true_false_must_have_exactly_two_options():
    """TRUE_FALSE question with 3 options raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        QuizQuestionSpec(
            question_number=1,
            question_type=QuestionType.TRUE_FALSE,
            question_text="Is this valid?",
            options=["True", "False", "Maybe"],
            correct_answer="True",
            explanation="Invalid options count.",
            target_concept_id=uuid4(),
            source_chunk_id=uuid4(),
        )
    assert "TRUE_FALSE questions must contain exactly 2 options" in str(exc_info.value)


def test_quiz_spec_questions_bounds():
    """questions count must be between 4 and 8."""
    dummy_q = QuizQuestionSpec(
        question_number=1,
        question_type=QuestionType.TRUE_FALSE,
        question_text="Statement to evaluate.",
        options=["True", "False"],
        correct_answer="True",
        explanation="Valid explanation meeting minimum length.",
        target_concept_id=uuid4(),
        source_chunk_id=uuid4(),
    )

    # < 4 questions rejected
    with pytest.raises(ValidationError) as exc_info:
        QuizSpec(
            passing_score_percentage=70,
            questions=[dummy_q, dummy_q, dummy_q],
        )
    assert "questions" in str(exc_info.value)

    # > 8 questions rejected
    with pytest.raises(ValidationError) as exc_info:
        QuizSpec(
            passing_score_percentage=70,
            questions=[dummy_q] * 9,
        )
    assert "questions" in str(exc_info.value)


def test_practical_exercise_rubric_bounds():
    """rubric_criteria must have at least 2 criteria."""
    with pytest.raises(ValidationError) as exc_info:
        PracticalExerciseSpec(
            prompt="Develop a comprehensive cryptographic configuration satisfying enterprise constraints.",
            deliverable_description="Working Python configuration script and test assertions.",
            rubric_criteria=[
                RubricCriterionSpec(
                    criterion="Code Implementation",
                    points=100,
                    description="Flawless code with complete tests.",
                )
            ],  # Only 1 criterion (< 2)
        )
    assert "rubric_criteria" in str(exc_info.value)


def test_assessment_package_output_valid():
    """Complete AssessmentPackageOutput satisfies root Contract 5."""
    dummy_q = QuizQuestionSpec(
        question_number=1,
        question_type=QuestionType.TRUE_FALSE,
        question_text="Statement to evaluate.",
        options=["True", "False"],
        correct_answer="True",
        explanation="Valid explanation meeting minimum length.",
        target_concept_id=uuid4(),
        source_chunk_id=uuid4(),
    )

    package = AssessmentPackageOutput(
        lesson_id=uuid4(),
        quiz=QuizSpec(
            passing_score_percentage=70,
            questions=[dummy_q, dummy_q, dummy_q, dummy_q],
        ),
        practical_exercise=PracticalExerciseSpec(
            prompt="Implement an automated key rotation policy for enterprise microservices.",
            deliverable_description="Python module with integration tests and configuration YAML.",
            rubric_criteria=[
                RubricCriterionSpec(criterion="Key Rotation Logic", points=50, description="Correct rotation intervals."),
                RubricCriterionSpec(criterion="Error Handling", points=50, description="Graceful recovery."),
            ],
        ),
    )

    assert package.quiz.passing_score_percentage == 70
    assert len(package.quiz.questions) == 4
    assert len(package.practical_exercise.rubric_criteria) == 2
