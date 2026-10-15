"""
Eduvance AI - Assessment Agent Data Contracts
WBS 3.5 - Assessment Schemas

Defines Pydantic v2 validation models strictly adhering to:
- Contract 5 (Assessment Agent) from WBS 2.1 (Architecture & Contracts)
- Database entity representations (Database/models/all_models.py: Quiz, QuizQuestion, PracticalExercise)

Owner: Member 3 (Generative Media and Assessment Engineer)
"""

from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuestionType(str, Enum):
    MCQ = "MCQ"
    TRUE_FALSE = "TRUE_FALSE"


class QuizQuestionSpec(BaseModel):
    """
    Individual quiz question grounded in a target concept and source chunk.
    Directly conforms to WBS 2.1 Contract 5 (AssessmentPackageOutput.quiz.questions[]).
    """
    model_config = ConfigDict(from_attributes=True)

    question_number: int = Field(
        ge=1,
        description="1-indexed sequence order of the question in the quiz",
    )
    question_type: QuestionType = Field(
        description="Format of the question: MCQ (multiple choice) or TRUE_FALSE",
    )
    question_text: str = Field(
        min_length=10,
        description="Clear, unambiguous assessment question prompt",
    )
    options: List[str] = Field(
        min_length=2,
        max_length=4,
        description="2 to 4 answer choices (exactly 2 for TRUE_FALSE, up to 4 for MCQ)",
    )
    correct_answer: str = Field(
        description="The strictly correct answer string matching one of the options",
    )
    explanation: str = Field(
        min_length=10,
        description="Pedagogical explanation detailing why the answer is correct",
    )
    target_concept_id: UUID = Field(
        description="UUID reference to the concept being assessed",
    )
    source_chunk_id: UUID = Field(
        description="UUID reference to the source chunk providing citation evidence",
    )

    @model_validator(mode="after")
    def validate_correct_answer_in_options(self) -> "QuizQuestionSpec":
        """Ensures the correct answer is explicitly present in the options list."""
        if self.correct_answer not in self.options:
            raise ValueError(
                f"correct_answer '{self.correct_answer}' must be one of the provided options: {self.options}"
            )
        if self.question_type == QuestionType.TRUE_FALSE and len(self.options) != 2:
            raise ValueError("TRUE_FALSE questions must contain exactly 2 options ('True' and 'False').")
        return self


class QuizSpec(BaseModel):
    """
    Quiz package containing 4 to 8 questions and passing score criteria.
    Directly conforms to WBS 2.1 Contract 5 (AssessmentPackageOutput.quiz).
    """
    model_config = ConfigDict(from_attributes=True)

    passing_score_percentage: int = Field(
        ge=50,
        le=100,
        default=70,
        description="Passing grade threshold in percentage (default: 70%)",
    )
    questions: List[QuizQuestionSpec] = Field(
        min_length=4,
        max_length=8,
        description="List of 4 to 8 assessment questions",
    )


class RubricCriterionSpec(BaseModel):
    """Grading rubric criterion for a practical exercise."""
    model_config = ConfigDict(from_attributes=True)

    criterion: str = Field(
        min_length=3,
        description="Title of the rubric criterion (e.g. 'Authentication Implementation')",
    )
    points: int = Field(
        ge=1,
        description="Point allocation for this criterion",
    )
    description: str = Field(
        min_length=10,
        description="Performance expectations required to earn full points",
    )


class PracticalExerciseSpec(BaseModel):
    """
    Hands-on real-world application challenge with starter code and rubric.
    Directly conforms to WBS 2.1 Contract 5 (AssessmentPackageOutput.practical_exercise).
    """
    model_config = ConfigDict(from_attributes=True)

    prompt: str = Field(
        min_length=20,
        description="Scenario-based problem statement and challenge description",
    )
    deliverable_description: str = Field(
        min_length=15,
        description="Expected submission artifact (e.g. 'Python script', 'Config file', 'Report')",
    )
    starter_template: Optional[str] = Field(
        default=None,
        description="Code scaffolding, starter boilerplate, or document template",
    )
    rubric_criteria: List[RubricCriterionSpec] = Field(
        min_length=2,
        description="At least 2 measurable evaluation criteria",
    )


class AssessmentPackageOutput(BaseModel):
    """
    Root contract output produced by the Assessment Agent.
    Strictly conforms to WBS 2.1 Contract 5 schema specification.
    """
    model_config = ConfigDict(from_attributes=True)

    lesson_id: UUID = Field(
        description="UUID of the parent lesson",
    )
    quiz: QuizSpec = Field(
        description="Interactive quiz specification",
    )
    practical_exercise: PracticalExerciseSpec = Field(
        description="Hands-on practical application challenge",
    )


# ---------------------------------------------------------
# Interactive Evaluation & Learner Scoring Schemas
# ---------------------------------------------------------

class QuizSubmission(BaseModel):
    """Learner's submission for an assessment quiz."""
    lesson_id: UUID
    answers: Dict[int, str] = Field(
        description="Mapping of question_number to learner's selected answer string",
    )


class QuestionEvaluation(BaseModel):
    """Evaluation result for an individual quiz question."""
    question_number: int
    question_text: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str
    target_concept_id: UUID
    source_chunk_id: UUID


class QuizResult(BaseModel):
    """Comprehensive evaluation score and concept mastery diagnostics."""
    lesson_id: UUID
    total_questions: int
    correct_count: int
    score_percentage: float
    passed: bool
    passing_score_percentage: int
    evaluations: List[QuestionEvaluation]
    mastered_concept_ids: List[UUID]
    revision_recommended_concept_ids: List[UUID]
    recommendation_message: str
