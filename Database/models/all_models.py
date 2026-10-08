"""
Eduvance AI - Complete SQLAlchemy 2.0 ORM Models

Implements all 14 relational entities specified in WBS 2.1 Section 7.
Every model uses UUID primary keys and strict foreign-key cascades to
guarantee end-to-end source traceability from content chunks through
lessons, quizzes, and tutor responses.

Reference: WBS 2.1 Sections 6-7 (ERD & Table Specifications)
Owner: Member 1 (Project Manager & Backend/Deployment Engineer)
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship

from Database.session import Base


# ── Helper: UTC Timestamp ─────────────────────────────────────────────
def _utcnow():
    return datetime.now(timezone.utc)


def _new_uuid():
    return str(uuid.uuid4())


# ══════════════════════════════════════════════════════════════════════
# 7.1  USERS
# ══════════════════════════════════════════════════════════════════════
class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(String(30), nullable=False, default="LEARNER")  # LEARNER | INSTRUCTOR | ADMIN
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    courses = relationship("Course", back_populates="owner", cascade="all, delete-orphan")
    learner_events = relationship("LearnerEvent", back_populates="user", cascade="all, delete-orphan")
    lesson_progress = relationship("LessonProgress", back_populates="user", cascade="all, delete-orphan")
    concept_mastery = relationship("ConceptMastery", back_populates="user", cascade="all, delete-orphan")


# ══════════════════════════════════════════════════════════════════════
# 7.2  COURSES
# ══════════════════════════════════════════════════════════════════════
class Course(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False, default="DRAFT")
    # Status values: DRAFT | EXTRACTING | EXTRACTED | DESIGNING_COURSE |
    #   PENDING_APPROVAL | GENERATING_ASSETS | ACTIVE | FAILED
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    owner = relationship("User", back_populates="courses")
    documents = relationship("Document", back_populates="course", cascade="all, delete-orphan")
    modules = relationship("Module", back_populates="course", cascade="all, delete-orphan")
    concepts = relationship("Concept", back_populates="course", cascade="all, delete-orphan")
    workflow_tasks = relationship("WorkflowTask", back_populates="course", cascade="all, delete-orphan")
    project_brief = relationship("ProjectBrief", back_populates="course", uselist=False, cascade="all, delete-orphan")
    learner_events = relationship("LearnerEvent", back_populates="course", cascade="all, delete-orphan")


# ══════════════════════════════════════════════════════════════════════
# 7.3  DOCUMENTS
# ══════════════════════════════════════════════════════════════════════
class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False)
    page_count = Column(Integer, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    upload_status = Column(String(30), nullable=False, default="UPLOADED")  # UPLOADED | EXTRACTED | FAILED
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    course = relationship("Course", back_populates="documents")
    chunks = relationship("ContentChunk", back_populates="document", cascade="all, delete-orphan")


# ══════════════════════════════════════════════════════════════════════
# 7.4  CONTENT CHUNKS
# ══════════════════════════════════════════════════════════════════════
class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=False)
    text_content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False)
    embedding_id = Column(String(100), nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    quiz_questions = relationship("QuizQuestion", back_populates="source_chunk")


# ══════════════════════════════════════════════════════════════════════
# 7.5  CONCEPTS
# ══════════════════════════════════════════════════════════════════════
class Concept(Base):
    __tablename__ = "concepts"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    difficulty = Column(String(20), default="BEGINNER")  # BEGINNER | INTERMEDIATE | ADVANCED
    prerequisite_concept_ids = Column(JSON, default=list)
    source_chunk_ids = Column(JSON, default=list)

    # Relationships
    course = relationship("Course", back_populates="concepts")
    quiz_questions = relationship("QuizQuestion", back_populates="target_concept")
    concept_mastery = relationship("ConceptMastery", back_populates="concept", cascade="all, delete-orphan")


# ══════════════════════════════════════════════════════════════════════
# 7.6  MODULES
# ══════════════════════════════════════════════════════════════════════
class Module(Base):
    __tablename__ = "modules"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    course = relationship("Course", back_populates="modules")
    lessons = relationship("Lesson", back_populates="module", cascade="all, delete-orphan")


# ══════════════════════════════════════════════════════════════════════
# 7.7  LESSONS
# ══════════════════════════════════════════════════════════════════════
class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    module_id = Column(String(36), ForeignKey("modules.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    sequence_order = Column(Integer, nullable=False)
    estimated_minutes = Column(Integer, default=10)
    learning_objectives = Column(JSON, nullable=False, default=list)
    target_concept_ids = Column(JSON, nullable=False, default=list)
    source_chunk_ids = Column(JSON, nullable=False, default=list)

    # Relationships
    module = relationship("Module", back_populates="lessons")
    video_asset = relationship("VideoAsset", back_populates="lesson", uselist=False, cascade="all, delete-orphan")
    quiz = relationship("Quiz", back_populates="lesson", uselist=False, cascade="all, delete-orphan")
    practical_exercises = relationship("PracticalExercise", back_populates="lesson", cascade="all, delete-orphan")
    lesson_progress = relationship("LessonProgress", back_populates="lesson", cascade="all, delete-orphan")
    learner_events = relationship("LearnerEvent", back_populates="lesson")


# ══════════════════════════════════════════════════════════════════════
# 7.8  VIDEO ASSETS
# ══════════════════════════════════════════════════════════════════════
class VideoAsset(Base):
    __tablename__ = "video_assets"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, unique=True)
    script_json = Column(JSON, nullable=False)
    slide_deck_json = Column(JSON, nullable=False)
    audio_path = Column(Text, nullable=True)
    srt_subtitles_path = Column(Text, nullable=True)
    video_path = Column(Text, nullable=True)
    duration_seconds = Column(Integer, default=0)
    generation_status = Column(String(30), default="PENDING")  # PENDING | PROCESSING | COMPLETED | FAILED
    error_message = Column(Text, nullable=True)

    # Relationships
    lesson = relationship("Lesson", back_populates="video_asset")


# ══════════════════════════════════════════════════════════════════════
# 7.9  QUIZZES & QUIZ QUESTIONS
# ══════════════════════════════════════════════════════════════════════
class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, unique=True)
    passing_score = Column(Integer, default=70)

    # Relationships
    lesson = relationship("Lesson", back_populates="quiz")
    questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    quiz_id = Column(String(36), ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False)  # MCQ | TRUE_FALSE
    options = Column(JSON, nullable=False)
    correct_answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    target_concept_id = Column(String(36), ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True)
    source_chunk_id = Column(String(36), ForeignKey("content_chunks.id", ondelete="SET NULL"), nullable=True)
    sequence_order = Column(Integer, nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="questions")
    target_concept = relationship("Concept", back_populates="quiz_questions")
    source_chunk = relationship("ContentChunk", back_populates="quiz_questions")


# ══════════════════════════════════════════════════════════════════════
# 7.10  PRACTICAL EXERCISES
# ══════════════════════════════════════════════════════════════════════
class PracticalExercise(Base):
    __tablename__ = "practical_exercises"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    deliverable_description = Column(Text, nullable=False)
    starter_template = Column(Text, nullable=True)
    rubric_criteria = Column(JSON, nullable=False)

    # Relationships
    lesson = relationship("Lesson", back_populates="practical_exercises")


# ══════════════════════════════════════════════════════════════════════
# 7.11  PROJECT BRIEFS
# ══════════════════════════════════════════════════════════════════════
class ProjectBrief(Base):
    __tablename__ = "project_briefs"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    scenario_description = Column(Text, nullable=False)
    deliverables = Column(JSON, nullable=False)
    milestone_roadmap = Column(JSON, nullable=False)
    rubric = Column(JSON, nullable=False)

    # Relationships
    course = relationship("Course", back_populates="project_brief")


# ══════════════════════════════════════════════════════════════════════
# 7.12  LEARNER EVENTS (Immutable append-only audit log)
# ══════════════════════════════════════════════════════════════════════
class LearnerEvent(Base):
    __tablename__ = "learner_events"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="SET NULL"), nullable=True)
    event_type = Column(String(50), nullable=False)
    # Event types: VIDEO_WATCHED | TUTOR_QUERY | QUIZ_ATTEMPT | REVISION_CLICKED
    payload = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    user = relationship("User", back_populates="learner_events")
    course = relationship("Course", back_populates="learner_events")
    lesson = relationship("Lesson", back_populates="learner_events")


# ══════════════════════════════════════════════════════════════════════
# 7.13  LESSON PROGRESS & CONCEPT MASTERY
# ══════════════════════════════════════════════════════════════════════
class LessonProgress(Base):
    __tablename__ = "lesson_progress"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lesson_id = Column(String(36), ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="NOT_STARTED")
    # NOT_STARTED | IN_PROGRESS | COMPLETED
    video_completed = Column(Boolean, default=False)
    quiz_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow)

    # Relationships
    user = relationship("User", back_populates="lesson_progress")
    lesson = relationship("Lesson", back_populates="lesson_progress")


class ConceptMastery(Base):
    __tablename__ = "concept_mastery"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = Column(String(36), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    mastery_score = Column(Float, default=0.0)
    needs_revision = Column(Boolean, default=False)
    last_evaluated_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    # Relationships
    user = relationship("User", back_populates="concept_mastery")
    concept = relationship("Concept", back_populates="concept_mastery")


# ══════════════════════════════════════════════════════════════════════
# 7.14  WORKFLOW TASKS (Async job tracking with retry policy)
# ══════════════════════════════════════════════════════════════════════
class WorkflowTask(Base):
    __tablename__ = "workflow_tasks"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    course_id = Column(String(36), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)
    # EXTRACTION | COURSE_DESIGN | VIDEO_GEN | QUIZ_GEN | RAG_INDEX
    status = Column(String(30), nullable=False, default="PENDING")
    # PENDING | RUNNING | COMPLETED | FAILED
    retry_count = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    course = relationship("Course", back_populates="workflow_tasks")

