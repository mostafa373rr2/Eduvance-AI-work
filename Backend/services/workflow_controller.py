"""
Eduvance AI - Central Workflow Controller & State Machine
WBS 4.1 - Course Lifecycle & Async Job Runner

Orchestrates the asynchronous agent workflow:
UPLOADED -> EXTRACTING -> EXTRACTED -> DESIGNING_COURSE -> PENDING_APPROVAL -> GENERATING_ASSETS -> ACTIVE
Tracks subtask lifecycles, manages bounded retry policies (max 2 retries), and executes asset pipelines.

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from Backend.core.progress_schemas import WorkflowStatusResponse, WorkflowTaskResponse
from Database.models.all_models import (
    Course,
    Lesson,
    Module,
    WorkflowTask,
    _utcnow,
)


class WorkflowController:
    """
    Central workflow state machine and task tracking orchestrator.
    """

    MAX_RETRIES = 2

    VALID_TRANSITIONS = {
        "DRAFT": ["EXTRACTING", "FAILED"],
        "UPLOADED": ["EXTRACTING", "FAILED"],
        "EXTRACTING": ["EXTRACTED", "FAILED"],
        "EXTRACTED": ["DESIGNING_COURSE", "FAILED"],
        "DESIGNING_COURSE": ["PENDING_APPROVAL", "FAILED"],
        "PENDING_APPROVAL": ["GENERATING_ASSETS", "DESIGNING_COURSE", "FAILED"],
        "GENERATING_ASSETS": ["ACTIVE", "ASSETS_FAILED", "PENDING_APPROVAL", "FAILED"],
        "ASSETS_FAILED": ["GENERATING_ASSETS", "PENDING_APPROVAL", "FAILED"],
        "ACTIVE": ["ARCHIVED", "GENERATING_ASSETS"],
        "FAILED": ["DRAFT", "EXTRACTING", "DESIGNING_COURSE"],
    }

    def transition_course_status(
        self,
        session: Session,
        course_id: UUID,
        target_status: str,
    ) -> Course:
        """
        Validates and transitions course state machine according to architectural constraints.
        """
        str_course_id = str(course_id)
        course = session.query(Course).filter(Course.id == str_course_id).first()
        if not course:
            raise ValueError(f"Course with ID '{course_id}' not found.")

        current = course.status
        allowed = self.VALID_TRANSITIONS.get(current, [])

        if target_status not in allowed and target_status != current:
            raise ValueError(
                f"Invalid course state transition from '{current}' to '{target_status}'. "
                f"Allowed target states: {allowed}"
            )

        course.status = target_status
        course.updated_at = _utcnow()
        session.commit()
        session.refresh(course)
        return course

    def create_task(
        self,
        session: Session,
        course_id: UUID,
        task_type: str,
    ) -> WorkflowTask:
        """Creates a new pending workflow task."""
        str_course_id = str(course_id)
        task = WorkflowTask(
            course_id=str_course_id,
            task_type=task_type.upper(),
            status="PENDING",
            retry_count=0,
            started_at=None,
            completed_at=None,
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    def start_task(self, session: Session, task_id: str) -> WorkflowTask:
        """Marks a task as RUNNING and stamps started_at."""
        task = session.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            raise ValueError(f"WorkflowTask '{task_id}' not found.")

        task.status = "RUNNING"
        task.started_at = _utcnow()
        session.commit()
        session.refresh(task)
        return task

    def complete_task(self, session: Session, task_id: str) -> WorkflowTask:
        """Marks a task as COMPLETED and stamps completed_at."""
        task = session.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            raise ValueError(f"WorkflowTask '{task_id}' not found.")

        task.status = "COMPLETED"
        task.completed_at = _utcnow()
        session.commit()
        session.refresh(task)
        return task

    def fail_task(
        self,
        session: Session,
        task_id: str,
        error_log: str,
    ) -> WorkflowTask:
        """
        Handles task failure: increments retry_count and re-queues if within MAX_RETRIES.
        If retry budget is exhausted, sets status to FAILED and updates Course status.
        """
        task = session.query(WorkflowTask).filter(WorkflowTask.id == task_id).first()
        if not task:
            raise ValueError(f"WorkflowTask '{task_id}' not found.")

        task.retry_count += 1
        task.error_log = error_log

        if task.retry_count <= self.MAX_RETRIES:
            # Re-queue for retry
            task.status = "PENDING"
        else:
            task.status = "FAILED"
            task.completed_at = _utcnow()

            # Course-level status degradation on exhausted retries
            course = session.query(Course).filter(Course.id == task.course_id).first()
            if course:
                if course.status == "GENERATING_ASSETS":
                    course.status = "ASSETS_FAILED"
                else:
                    course.status = "FAILED"

        session.commit()
        session.refresh(task)
        return task

    def get_workflow_status(
        self,
        session: Session,
        course_id: UUID,
    ) -> WorkflowStatusResponse:
        """Summarizes real-time workflow execution progress and task list for a course."""
        str_course_id = str(course_id)
        course = session.query(Course).filter(Course.id == str_course_id).first()
        if not course:
            raise ValueError(f"Course with ID '{course_id}' not found.")

        tasks = (
            session.query(WorkflowTask)
            .filter(WorkflowTask.course_id == str_course_id)
            .order_by(WorkflowTask.started_at.asc())
            .all()
        )

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "COMPLETED")
        failed = sum(1 for t in tasks if t.status == "FAILED")

        pct = round((completed / total) * 100.0, 1) if total > 0 else (100.0 if course.status == "ACTIVE" else 0.0)

        task_responses = [WorkflowTaskResponse.model_validate(t) for t in tasks]

        return WorkflowStatusResponse(
            course_id=str_course_id,
            course_status=course.status,
            total_tasks=total,
            completed_tasks=completed,
            failed_tasks=failed,
            progress_percentage=pct,
            tasks=task_responses,
        )

    def trigger_asset_generation(
        self,
        session: Session,
        course_id: UUID,
        simulate_execution: bool = True,
    ) -> Course:
        """
        Transitions course from PENDING_APPROVAL to GENERATING_ASSETS,
        queues asset generation tasks, and completes them to reach ACTIVE status.
        """
        str_course_id = str(course_id)
        course = session.query(Course).filter(Course.id == str_course_id).first()
        if not course:
            raise ValueError(f"Course with ID '{course_id}' not found.")

        if course.status != "PENDING_APPROVAL":
            raise ValueError(
                f"Course cannot trigger asset generation: Current status is '{course.status}', "
                f"expected 'PENDING_APPROVAL'."
            )

        # 1. State transition
        self.transition_course_status(session, course_id, "GENERATING_ASSETS")

        # 2. Fetch all lessons
        modules = session.query(Module).filter(Module.course_id == str_course_id).all()
        mod_ids = [m.id for m in modules]
        lessons = session.query(Lesson).filter(Lesson.module_id.in_(mod_ids)).all() if mod_ids else []

        # 3. Create workflow tasks for Video, Assessment, and RAG Indexing
        tasks: List[WorkflowTask] = []
        for les in lessons:
            t_vid = self.create_task(session, course_id, f"VIDEO_GEN_{les.id}")
            t_quiz = self.create_task(session, course_id, f"QUIZ_GEN_{les.id}")
            tasks.extend([t_vid, t_quiz])

        t_rag = self.create_task(session, course_id, "RAG_INDEX")
        tasks.append(t_rag)

        # 4. If execution requested, process tasks to completion
        if simulate_execution:
            for t in tasks:
                self.start_task(session, t.id)
                self.complete_task(session, t.id)

            # All assets completed -> transition to ACTIVE
            course = self.transition_course_status(session, course_id, "ACTIVE")

        return course

