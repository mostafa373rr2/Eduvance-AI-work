"""
Eduvance AI - Course Design Data Contracts
WBS 3.3 - Course Designer Agent Schemas

Defines Pydantic v2 validation models strictly adhering to:
- Contract 2 (Course Designer Agent) from WBS 2.1 (Architecture & Contracts)
- Database entity representations (Database/models/all_models.py: Module, Lesson)

Owner: Member 2 (Content and RAG Engineer)
"""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LessonDesign(BaseModel):
    """
    Structured lesson unit within a course module.
    Directly conforms to WBS 2.1 Contract 2 (CourseDesignOutput.modules[].lessons[]).
    """
    model_config = ConfigDict(from_attributes=True)

    lesson_sequence: int = Field(
        ge=1,
        description="1-indexed sequence order of the lesson within its parent module",
    )
    title: str = Field(
        min_length=2,
        max_length=255,
        description="Pedagogically descriptive lesson title",
    )
    estimated_minutes: int = Field(
        ge=5,
        le=30,
        default=10,
        description="Estimated completion time in minutes (constrained to 5-30 minutes)",
    )
    learning_objectives: List[str] = Field(
        min_length=2,
        description="At least 2 measurable learning objectives phrased using Bloom's taxonomy action verbs",
    )
    target_concept_ids: List[UUID] = Field(
        min_length=1,
        description="UUID references to domain concepts taught and reinforced in this lesson",
    )
    source_chunk_ids: List[UUID] = Field(
        min_length=1,
        description="UUID references to source document chunks providing grounding evidence for this lesson",
    )


class ModuleDesign(BaseModel):
    """
    High-level thematic course module grouping related lessons.
    Directly conforms to WBS 2.1 Contract 2 (CourseDesignOutput.modules[]).
    """
    model_config = ConfigDict(from_attributes=True)

    module_sequence: int = Field(
        ge=1,
        description="1-indexed sequence order of the module within the course",
    )
    title: str = Field(
        min_length=2,
        max_length=255,
        description="Thematic module title",
    )
    description: str = Field(
        min_length=5,
        description="Overview of topics and competencies covered within this module",
    )
    lessons: List[LessonDesign] = Field(
        min_length=1,
        max_length=3,
        description="Structured lessons contained within this module (constrained to 1-3 lessons)",
    )


class CourseDesignOutput(BaseModel):
    """
    Root contract output produced by the Course Designer Agent.
    Strictly conforms to WBS 2.1 Contract 2 schema specification.
    """
    model_config = ConfigDict(from_attributes=True)

    course_title: str = Field(
        min_length=5,
        max_length=255,
        description="Formal title of the generated course",
    )
    description: str = Field(
        min_length=20,
        description="Comprehensive course overview describing intended audience, outcomes, and syllabus scope",
    )
    modules: List[ModuleDesign] = Field(
        min_length=2,
        max_length=4,
        description="Curriculum modules composing the course (constrained to 2-4 modules)",
    )


class LessonUpdate(BaseModel):
    """Schema for instructor edits to a specific lesson prior to approval."""
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    estimated_minutes: Optional[int] = Field(default=None, ge=5, le=30)
    learning_objectives: Optional[List[str]] = Field(default=None, min_length=2)
    target_concept_ids: Optional[List[UUID]] = None
    source_chunk_ids: Optional[List[UUID]] = None


class ModuleUpdate(BaseModel):
    """Schema for instructor edits to a module prior to approval."""
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = Field(default=None, min_length=5)
