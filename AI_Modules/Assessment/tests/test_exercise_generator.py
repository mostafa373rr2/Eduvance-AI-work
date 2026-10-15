"""
Eduvance AI - Practical Exercise Generator Tests
WBS 3.5 - Hands-on Challenge & Rubric Synthesis

Tests:
- Generation of Contract 5 compliant PracticalExerciseSpec objects.
- Realistic problem prompts aligned with lesson concepts.
- Starter code template synthesis.
- Multi-criteria rubric formulation (summing to 100 points).

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from AI_Modules.Assessment.exercise_generator import PracticalExerciseGenerator
from AI_Modules.Assessment.schemas import PracticalExerciseSpec


def test_generate_practical_exercise_satisfies_contract_5(mock_assessment_lesson_data):
    """Verifies generated exercise meets Contract 5 criteria and rubric point conventions."""
    generator = PracticalExerciseGenerator()
    exercise = generator.generate_exercise(
        lesson_id=mock_assessment_lesson_data["lesson_id"],
        lesson_title=mock_assessment_lesson_data["lesson_title"],
        learning_objectives=mock_assessment_lesson_data["learning_objectives"],
        concepts=mock_assessment_lesson_data["concepts"],
        chunks=mock_assessment_lesson_data["chunks"],
    )

    assert isinstance(exercise, PracticalExerciseSpec)
    assert len(exercise.prompt) >= 20
    assert len(exercise.deliverable_description) >= 15
    assert exercise.starter_template is not None
    assert "def " in exercise.starter_template
    assert len(exercise.rubric_criteria) >= 2

    # Check total points sum to 100
    total_points = sum(c.points for c in exercise.rubric_criteria)
    assert total_points == 100

    # Check alignment with target concepts
    top_concept_name = mock_assessment_lesson_data["concepts"][0].name
    assert top_concept_name in exercise.prompt or top_concept_name in exercise.starter_template
