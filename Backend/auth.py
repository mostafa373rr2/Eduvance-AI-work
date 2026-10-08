"""Account APIs and shared authentication dependencies."""

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass
from typing import Callable

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from Backend.core.config import Settings
from Database.models.all_models import User


class Credentials(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr = Field(max_length=255)
    password: SecretStr

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value):
        return value.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        password = value.get_secret_value()
        if not 12 <= len(password) or len(password.encode("utf-8")) > 72:
            raise ValueError("Password must contain at least 12 characters and at most 72 UTF-8 bytes")
        return value


class Registration(Credentials):
    full_name: str = Field(min_length=1, max_length=150)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, value):
        if not value.strip():
            raise ValueError("Full name must not be blank")
        return value.strip()


class PublicUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@dataclass(frozen=True)
class AuthDependencies:
    configured: Callable
    database: Callable
    current_user: Callable
    unauthorized: Callable


def auth_dependencies(session_factory: sessionmaker, config: Settings) -> AuthDependencies:
    bearer = HTTPBearer(auto_error=False)

    def configured():
        if (len(config.SECRET_KEY.encode("utf-8")) < 32
                or config.SECRET_KEY == "eduvance-secret-key-change-in-production-for-security"
                or config.ALGORITHM != "HS256"
                or config.ACCESS_TOKEN_EXPIRE_MINUTES <= 0):
            raise HTTPException(503, "Authentication is not configured")

    def database():
        with session_factory() as session:
            yield session

    def unauthorized():
        return HTTPException(401, "Invalid credentials", headers={"WWW-Authenticate": "Bearer"})

    def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
                     session: Session = Depends(database), _=Depends(configured)):
        if credentials is None:
            raise unauthorized()
        try:
            claims = jwt.decode(credentials.credentials, config.SECRET_KEY,
                                algorithms=["HS256"], audience="eduvance-api",
                                issuer="eduvance", options={"require_exp": True,
                                "require_iat": True, "require_sub": True})
            if claims.get("token_type") != "access":
                raise unauthorized()
            user = session.get(User, claims["sub"])
        except JWTError:
            raise unauthorized() from None
        if user is None:
            raise unauthorized()
        return user

    return AuthDependencies(configured, database, current_user, unauthorized)


def auth_router(dependencies: AuthDependencies, config: Settings) -> APIRouter:
    router = APIRouter(prefix="/auth", tags=["Accounts"])
    configured = dependencies.configured
    database = dependencies.database
    current_user = dependencies.current_user
    unauthorized = dependencies.unauthorized
    # Same bcrypt work on unknown-account and wrong-password login attempts.
    dummy_hash = bcrypt.hashpw(b"dummy-account-password", bcrypt.gensalt())

    @router.post("/register", response_model=PublicUser, status_code=201,
                 dependencies=[Depends(configured)])
    def register(payload: Registration, session: Session = Depends(database)):
        if session.scalar(select(User).where(User.email == payload.email)) is not None:
            raise HTTPException(409, "Email already registered")
        user = User(email=payload.email, full_name=payload.full_name, role="LEARNER",
                    password_hash=bcrypt.hashpw(payload.password.get_secret_value().encode("utf-8"),
                                                bcrypt.gensalt()).decode("ascii"))
        session.add(user)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(409, "Account could not be registered") from None
        session.refresh(user)
        return user

    @router.post("/login", response_model=TokenResponse, dependencies=[Depends(configured)])
    def login(payload: Credentials, response: Response, session: Session = Depends(database)):
        user = session.scalar(select(User).where(User.email == payload.email))
        stored_hash = user.password_hash.encode("utf-8") if user else dummy_hash
        try:
            valid = bcrypt.checkpw(payload.password.get_secret_value().encode("utf-8"), stored_hash)
        except ValueError:
            valid = False
        if not valid or user is None:
            raise unauthorized()
        now = datetime.now(timezone.utc)
        lifetime = config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        token = jwt.encode({"sub": user.id, "iat": now, "exp": now + timedelta(seconds=lifetime),
                            "iss": "eduvance", "aud": "eduvance-api", "token_type": "access"},
                           config.SECRET_KEY, algorithm="HS256")
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return TokenResponse(access_token=token, expires_in=lifetime)

    @router.get("/me", response_model=PublicUser)
    def me(response: Response, user: User = Depends(current_user)):
        response.headers["Cache-Control"] = "no-store"
        return user

    return router
