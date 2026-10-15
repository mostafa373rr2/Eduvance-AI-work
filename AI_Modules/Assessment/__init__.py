"""
Eduvance AI - Assessment Agent Module
WBS 3.5 - Automated Assessment Synthesis & Evaluation Engine

Exports quiz generation, hands-on practical exercise synthesis, deterministic grading,
and database persistence services conforming strictly to WBS 2.1 Contract 5.

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from .evaluator import QuizEvaluator
from .exercise_generator import PracticalExerciseGenerator
from .persistence import AssessmentPersistenceService
from .pipeline import AssessmentGenerationPipeline
from .quiz_generator import QuizGenerator
from .schemas import (
    AssessmentPackageOutput,
    PracticalExerciseSpec,
    QuestionEvaluation,
    QuestionType,
    QuizQuestionSpec,
    QuizResult,
    QuizSpec,
    QuizSubmission,
    RubricCriterionSpec,
)

__all__ = [
    "AssessmentGenerationPipeline",
    "QuizGenerator",
    "PracticalExerciseGenerator",
    "QuizEvaluator",
    "AssessmentPersistenceService",
    "AssessmentPackageOutput",
    "QuizSpec",
    "QuizQuestionSpec",
    "QuestionType",
    "PracticalExerciseSpec",
    "RubricCriterionSpec",
    "QuizSubmission",
    "QuizResult",
    "QuestionEvaluation",
]
