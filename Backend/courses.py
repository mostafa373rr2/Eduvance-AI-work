"""Authenticated course containers; content generation belongs to Member 2."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from Backend.auth import AuthDependencies
from Database.models.all_models import Course, User


class CourseCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=255)
    domain: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=10000)

    @field_validator("title", "domain")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Must not be blank")
        return value.strip()


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    domain: str
    description: str | None
    status: str
    created_at: datetime
    updated_at: datetime


def owned_course(session: Session, course_id: UUID, user_id: str) -> Course:
    """Filter ownership in the query; foreign and absent IDs both return 404."""
    course = session.scalar(select(Course).where(Course.id == str(course_id),
                                                 Course.user_id == user_id))
    if course is None:
        raise HTTPException(404, "Course not found")
    return course


def course_router(dependencies: AuthDependencies) -> APIRouter:
    router = APIRouter(prefix="/courses", tags=["Courses"])

    @router.post("", response_model=CourseResponse, status_code=201)
    def create_course(payload: CourseCreate, response: Response,
                      user: User = Depends(dependencies.current_user),
                      session: Session = Depends(dependencies.database)):
        course = Course(user_id=user.id, title=payload.title, domain=payload.domain,
                        description=payload.description, status="DRAFT")
        session.add(course)
        session.commit()
        session.refresh(course)
        response.headers["Cache-Control"] = "no-store"
        return course

    @router.get("", response_model=list[CourseResponse])
    def list_courses(response: Response, limit: int = Query(default=20, ge=1, le=100),
                     offset: int = Query(default=0, ge=0),
                     user: User = Depends(dependencies.current_user),
                     session: Session = Depends(dependencies.database)):
        response.headers["Cache-Control"] = "no-store"
        return session.scalars(select(Course).where(Course.user_id == user.id)
                               .order_by(Course.created_at.desc(), Course.id)
                               .offset(offset).limit(limit)).all()

    @router.get("/{course_id}", response_model=CourseResponse)
    def get_course(course_id: UUID, response: Response,
                   user: User = Depends(dependencies.current_user),
                   session: Session = Depends(dependencies.database)):
        course = owned_course(session, course_id, user.id)
        response.headers["Cache-Control"] = "no-store"
        return course

    return router
