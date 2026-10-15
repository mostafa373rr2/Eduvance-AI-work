"""
Eduvance AI - Learner Events REST API Router
WBS 4.1 - Telemetry Ingestion & Audit Log

Provides authenticated REST endpoints for logging learner events and querying telemetry.

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from Backend.auth import AuthDependencies
from Backend.core.progress_schemas import LearnerEventCreate, LearnerEventResponse
from Backend.services.event_service import EventService
from Database.models.all_models import Course, User


def event_router(dependencies: AuthDependencies) -> APIRouter:
    router = APIRouter(prefix="/events", tags=["Learner Events"])
    event_service = EventService()

    @router.post("", response_model=LearnerEventResponse, status_code=201)
    def record_learner_event(
        event_data: LearnerEventCreate,
        current_user: User = Depends(dependencies.current_user),
        session: Session = Depends(dependencies.database),
    ):
        """
        Ingests a learner telemetry event (VIDEO_WATCHED, QUIZ_ATTEMPT, TUTOR_QUERY)
        and synchronizes lesson completion and concept mastery states.
        """
        # Verify course exists
        course = session.query(Course).filter(Course.id == str(event_data.course_id)).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        try:
            event = event_service.ingest_event(
                session=session,
                user_id=UUID(current_user.id),
                event_data=event_data,
            )
            return event
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.get("/course/{course_id}", response_model=List[LearnerEventResponse])
    def list_course_events(
        course_id: UUID,
        limit: int = Query(default=50, ge=1, le=100),
        current_user: User = Depends(dependencies.current_user),
        session: Session = Depends(dependencies.database),
    ):
        """
        Queries learner interaction events for a given course container.
        """
        course = session.query(Course).filter(Course.id == str(course_id)).first()
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")

        events = event_service.get_course_events(
            session=session,
            course_id=course_id,
            user_id=UUID(current_user.id) if current_user.role == "LEARNER" else None,
            limit=limit,
        )
        return events

    return router

