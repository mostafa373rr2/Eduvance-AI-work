"""
Eduvance AI - Progress & Workflow REST API Router
WBS 4.1 - Contract 6 Endpoints & Workflow Lifecycle

Provides authenticated REST endpoints for:
- Querying Contract 6 ProgressEvaluationOutput (overall completion, concept mastery, recommendations)
- Inspecting real-time WorkflowStatusResponse (asynchronous job tracking)
- Approving course outlines to trigger asset generation pipelines

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from Backend.auth import AuthDependencies
from Backend.core.progress_schemas import (
    ProgressEvaluationOutput,
    WorkflowStatusResponse,
)
from Backend.courses import CourseResponse
from Backend.services.progress_engine import ProgressEngine
from Backend.services.workflow_controller import WorkflowController
from Database.models.all_models import Course, User


def progress_router(dependencies: AuthDependencies) -> APIRouter:
    router = APIRouter(prefix="/courses", tags=["Progress & Workflow"])
    progress_engine = ProgressEngine()
    workflow_controller = WorkflowController()

    @router.get("/{course_id}/progress", response_model=ProgressEvaluationOutput)
    def get_course_progress(
        course_id: UUID,
        current_user: User = Depends(dependencies.current_user),
        session: Session = Depends(dependencies.database),
    ):
        """
        Retrieves the Contract 6 ProgressEvaluationOutput for the authenticated learner.
        Includes overall completion percentage, concept mastery summary, and remedial recommendations.
        """
        course = session.query(Course).filter(Course.id == str(course_id)).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        try:
            progress_report = progress_engine.evaluate_course_progress(
                session=session,
                user_id=UUID(current_user.id),
                course_id=course_id,
            )
            return progress_report
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/{course_id}/workflow", response_model=WorkflowStatusResponse)
    def get_course_workflow_status(
        course_id: UUID,
        current_user: User = Depends(dependencies.current_user),
        session: Session = Depends(dependencies.database),
    ):
        """
        Queries asynchronous task progress and overall course generation lifecycle state.
        """
        course = session.query(Course).filter(Course.id == str(course_id)).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        status_report = workflow_controller.get_workflow_status(session, course_id)
        return status_report

    @router.post("/{course_id}/approve", response_model=CourseResponse)
    def approve_course_and_generate_assets(
        course_id: UUID,
        current_user: User = Depends(dependencies.current_user),
        session: Session = Depends(dependencies.database),
    ):
        """
        Instructor approves the generated curriculum outline.
        Transitions course to GENERATING_ASSETS, executes multimedia pipelines, and activates the course.
        """
        course = session.query(Course).filter(Course.id == str(course_id)).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        # Multi-tenant ownership check: only course owner or admin can approve
        if course.user_id != current_user.id and current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Forbidden: You do not own this course.")

        try:
            updated_course = workflow_controller.trigger_asset_generation(
                session=session,
                course_id=course_id,
                simulate_execution=True,
            )
            return updated_course
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router

