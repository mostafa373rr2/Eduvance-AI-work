"""
Eduvance AI - Learner Event Ingestion Service
WBS 4.1 - Telemetry & Progress Synchronization Engine

Ingests immutable learner telemetry events (VIDEO_WATCHED, QUIZ_ATTEMPT, TUTOR_QUERY)
and automatically updates lesson completion state and concept mastery scores.

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from Backend.core.progress_schemas import LearnerEventCreate
from Database.models.all_models import (
    ConceptMastery,
    Course,
    LearnerEvent,
    Lesson,
    LessonProgress,
    User,
    _utcnow,
)


class EventService:
    """
    Ingests learner interaction telemetry and synchronizes learning state.
    """

    PASSING_THRESHOLD = 70.0

    def ingest_event(
        self,
        session: Session,
        user_id: UUID,
        event_data: LearnerEventCreate,
    ) -> LearnerEvent:
        """
        Records an immutable learner event and dispatches progress updates.
        """
        str_user_id = str(user_id)
        str_course_id = str(event_data.course_id)
        str_lesson_id = str(event_data.lesson_id) if event_data.lesson_id else None

        # 1. Verify Course and User exist
        course = session.query(Course).filter(Course.id == str_course_id).first()
        if not course:
            raise ValueError(f"Course with ID '{event_data.course_id}' not found.")

        user = session.query(User).filter(User.id == str_user_id).first()
        if not user:
            raise ValueError(f"User with ID '{user_id}' not found.")

        # 2. Append immutable event to audit log
        db_event = LearnerEvent(
            user_id=str_user_id,
            course_id=str_course_id,
            lesson_id=str_lesson_id,
            event_type=event_data.event_type.upper(),
            payload=event_data.payload,
            created_at=_utcnow(),
        )
        session.add(db_event)
        session.flush()

        # 3. Synchronize Lesson Progress if event relates to a specific lesson
        if str_lesson_id:
            lesson = session.query(Lesson).filter(Lesson.id == str_lesson_id).first()
            if lesson:
                progress = (
                    session.query(LessonProgress)
                    .filter(
                        LessonProgress.user_id == str_user_id,
                        LessonProgress.lesson_id == str_lesson_id,
                    )
                    .first()
                )
                if not progress:
                    progress = LessonProgress(
                        user_id=str_user_id,
                        lesson_id=str_lesson_id,
                        status="NOT_STARTED",
                        video_completed=False,
                        quiz_completed=False,
                    )
                    session.add(progress)
                    session.flush()

                # Event-specific side-effects
                event_type = event_data.event_type.upper()

                if event_type == "VIDEO_WATCHED":
                    # Mark video completed if explicit flag or >= 80% watched
                    completed = event_data.payload.get("completed", False)
                    seconds = event_data.payload.get("seconds_watched", 0)
                    total = event_data.payload.get("total_duration", 1)
                    if completed or (total > 0 and (seconds / total) >= 0.8):
                        progress.video_completed = True

                elif event_type == "QUIZ_ATTEMPT":
                    passed = event_data.payload.get("passed", False)
                    score_pct = event_data.payload.get("score_percentage", 0.0)
                    if passed or score_pct >= self.PASSING_THRESHOLD:
                        progress.quiz_completed = True

                    # Update Concept Mastery if concept breakdown provided
                    concept_scores = event_data.payload.get("concept_scores", {})
                    for cid, cscore in concept_scores.items():
                        str_cid = str(cid)
                        cm = (
                            session.query(ConceptMastery)
                            .filter(
                                ConceptMastery.user_id == str_user_id,
                                ConceptMastery.concept_id == str_cid,
                            )
                            .first()
                        )
                        score_val = float(cscore)
                        needs_rev = score_val < self.PASSING_THRESHOLD

                        if not cm:
                            cm = ConceptMastery(
                                user_id=str_user_id,
                                concept_id=str_cid,
                                mastery_score=score_val,
                                needs_revision=needs_rev,
                                last_evaluated_at=_utcnow(),
                            )
                            session.add(cm)
                        else:
                            cm.mastery_score = score_val
                            cm.needs_revision = needs_rev
                            cm.last_evaluated_at = _utcnow()

                # Update composite completion status
                if progress.video_completed and progress.quiz_completed:
                    progress.status = "COMPLETED"
                elif progress.video_completed or progress.quiz_completed:
                    progress.status = "IN_PROGRESS"

                progress.updated_at = _utcnow()

        session.commit()
        session.refresh(db_event)
        return db_event

    def get_course_events(
        self,
        session: Session,
        course_id: UUID,
        user_id: Optional[UUID] = None,
        limit: int = 50,
    ) -> List[LearnerEvent]:
        """Queries historical learner event log with multi-user isolation."""
        query = session.query(LearnerEvent).filter(LearnerEvent.course_id == str(course_id))
        if user_id:
            query = query.filter(LearnerEvent.user_id == str(user_id))

        return query.order_by(LearnerEvent.created_at.desc()).limit(limit).all()

