"""
Eduvance AI - Course Designer Agent Module
WBS 3.3 - Course Curriculum & Syllabus Synthesis

Exports core course design schemas, generation engine, database persistence service,
and pipeline orchestrator conforming strictly to WBS 2.1 Contract 2.

Owner: Member 2 (Content and RAG Engineer)
"""

from .course_designer import CourseDesigner
from .persistence import CourseDesignPersistenceService
from .pipeline import CourseDesignPipeline
from .schemas import (
    CourseDesignOutput,
    LessonDesign,
    LessonUpdate,
    ModuleDesign,
    ModuleUpdate,
)

__all__ = [
    "CourseDesigner",
    "CourseDesignOutput",
    "ModuleDesign",
    "LessonDesign",
    "LessonUpdate",
    "ModuleUpdate",
    "CourseDesignPipeline",
    "CourseDesignPersistenceService",
]
