"""
Eduvance AI - Progress & Workflow Data Contracts
WBS 4.1 - Contract 6 Schemas & Telemetry Payloads

Defines Pydantic v2 validation models strictly adhering to:
- Contract 6 (Progress & Recommendation Engine) from WBS 2.1
- Learner Event Ingestion payloads (VIDEO_WATCHED, QUIZ_ATTEMPT, TUTOR_QUERY)
- WorkflowTask tracking and state machine representations

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ══════════════════════════════════════════════════════════════════════
# CONTRACT 6: PROGRESS & RECOMMENDATION ENGINE
# ══════════════════════════════════════════════════════════════════════

class ConceptMasteryItem(BaseModel):
    """Evaluation of an individual domain concept's mastery level."""
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID = Field(description="UUID of the assessed concept")
    concept_name: str = Field(description="Display title of the concept")
    score_percentage: float = Field(
        ge=0.0,
        le=100.0,
        description="Mastery score percentage achieved by the learner (0.0 to 100.0)",
    )
    needs_revision: bool = Field(
        description="True if score is below the 70% threshold, triggering remedial recommendation",
    )


class RecommendationItem(BaseModel):
    """Explainable revision recommendation for a specific lesson and concept."""
    model_config = ConfigDict(from_attributes=True)

    lesson_id: UUID = Field(description="UUID of the recommended lesson to review")
    lesson_title: str = Field(description="Title of the recommended lesson")
    trigger_concept: str = Field(description="Specific concept that triggered the revision")
    trigger_quiz_score: float = Field(description="Assessment score that fell below threshold")
    reason: str = Field(
        min_length=15,
        description="Explainable pedagogical reason describing why review is advised",
    )


class ProgressEvaluationOutput(BaseModel):
    """
    Root contract output produced by the Progress & Recommendation Engine.
    Strictly conforms to WBS 2.1 Contract 6 schema specification.
    """
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID = Field(description="UUID of the evaluated learner")
    course_id: UUID = Field(description="UUID of the parent course container")
    overall_completion_percentage: float = Field(
        ge=0.0,
        le=100.0,
        description="Proportion of completed lessons across the course (0.0 to 100.0%)",
    )
    concept_mastery_summary: List[ConceptMasteryItem] = Field(
        description="Summary of learner performance across all course domain concepts",
    )
    recommendations: List[RecommendationItem] = Field(
        description="Actionable remedial recommendations for concepts scoring under 70%",
    )


# ══════════════════════════════════════════════════════════════════════
# LEARNER TELEMETRY & EVENT INGESTION SCHEMAS
# ══════════════════════════════════════════════════════════════════════

class LearnerEventCreate(BaseModel):
    """Payload for submitting a learner telemetry event."""
    course_id: UUID
    lesson_id: Optional[UUID] = None
    event_type: str = Field(
        description="Event category: VIDEO_WATCHED | QUIZ_ATTEMPT | TUTOR_QUERY | REVISION_CLICKED",
    )
    payload: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event specific telemetry data (e.g. score, duration, query)",
    )


class LearnerEventResponse(BaseModel):
    """Serialized audit log record for an ingested learner event."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    course_id: str
    lesson_id: Optional[str] = None
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime


# ══════════════════════════════════════════════════════════════════════
# WORKFLOW CONTROLLER SCHEMAS
# ══════════════════════════════════════════════════════════════════════

class WorkflowTaskResponse(BaseModel):
    """Status metadata for an asynchronous agent workflow task."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    course_id: str
    task_type: str
    status: str
    retry_count: int
    error_log: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowStatusResponse(BaseModel):
    """Overall workflow progress and job status for a course."""
    course_id: str
    course_status: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    progress_percentage: float
    tasks: List[WorkflowTaskResponse]

