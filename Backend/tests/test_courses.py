"""Two-user isolation through the real account and course HTTP endpoints."""

from pathlib import Path
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from Backend.core.config import Settings
from Backend.main import create_app
from Database.models.all_models import Course


@pytest.fixture
def users():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    settings = Settings(_env_file=None, SECRET_KEY="test-only-course-signing-key-" * 3)
    with TestClient(create_app(engine, settings)) as client:
        accounts = []
        for name in ("alice", "bob"):
            credentials = {"email": f"{name}@example.com", "password": "valid-test-password"}
            registration = client.post("/api/v1/auth/register", json={**credentials, "full_name": name})
            assert registration.status_code == 201
            login = client.post("/api/v1/auth/login", json=credentials)
            assert login.status_code == 200
            accounts.append((registration.json()["id"],
                             {"Authorization": f"Bearer {login.json()['access_token']}"}))
        yield client, engine, accounts
    engine.dispose()


def test_two_users_can_only_list_and_read_owned_courses(users):
    client, engine, accounts = users
    created = []
    for index, (user_id, headers) in enumerate(accounts):
        assert client.get("/api/v1/courses", headers=headers).json() == []
        response = client.post("/api/v1/courses", headers=headers,
                               json={"title": f" Course {index} ", "domain": " Computing ",
                                     "description": "Private course"})
        assert response.status_code == 201
        course = response.json()
        assert course["status"] == "DRAFT"
        assert course["title"] == f"Course {index}"
        assert course["domain"] == "Computing"
        assert "user_id" not in course
        assert "password_hash" not in response.text
        assert response.headers["cache-control"] == "no-store"
        with Session(engine) as session:
            assert session.get(Course, course["id"]).user_id == user_id
        created.append(course)
    for index, (_, headers) in enumerate(accounts):
        response = client.get("/api/v1/courses", headers=headers)
        assert response.status_code == 200
        assert response.json() == [created[index]]
        own = client.get(f"/api/v1/courses/{created[index]['id']}", headers=headers)
        assert own.status_code == 200
        assert own.json() == created[index]
        foreign = client.get(f"/api/v1/courses/{created[1-index]['id']}", headers=headers)
        missing = client.get(f"/api/v1/courses/{uuid4()}", headers=headers)
        assert foreign.status_code == missing.status_code == 404
        assert foreign.json() == missing.json() == {"detail": "Course not found"}


def test_client_cannot_assign_owner_or_status_and_invalid_inputs_do_not_persist(users):
    client, engine, accounts = users
    payload = {"title": "Test", "domain": "Test"}
    invalid = [{"user_id": accounts[1][0]}, {"status": "ACTIVE"}, {"id": str(uuid4())},
               {"title": " "}, {"title": "x" * 256}, {"domain": " "},
               {"domain": "x" * 101}, {"description": "x" * 10001}]
    for change in invalid:
        assert client.post("/api/v1/courses", headers=accounts[0][1],
                           json={**payload, **change}).status_code == 422
    with Session(engine) as session:
        assert session.scalars(select(Course)).all() == []


def test_all_course_routes_require_valid_authentication(users):
    client, _, accounts = users
    created = client.post("/api/v1/courses", headers=accounts[0][1],
                          json={"title": "Test", "domain": "Test"}).json()
    for headers in ({}, {"Authorization": "Bearer invalid"}):
        assert client.post("/api/v1/courses", headers=headers,
                           json={"title": "Test", "domain": "Test"}).status_code == 401
        assert client.get("/api/v1/courses", headers=headers).status_code == 401
        assert client.get(f"/api/v1/courses/{created['id']}", headers=headers).status_code == 401


def test_pagination_and_path_validation(users):
    client, _, accounts = users
    headers = accounts[0][1]
    for index in range(3):
        assert client.post("/api/v1/courses", headers=headers,
                           json={"title": f"Course {index}", "domain": "Test"}).status_code == 201
    all_courses = client.get("/api/v1/courses", headers=headers).json()
    pages = [client.get(f"/api/v1/courses?limit=1&offset={index}", headers=headers).json()[0]
             for index in range(3)]
    assert pages == all_courses
    assert client.get("/api/v1/courses?offset=3", headers=headers).json() == []
    for query in ("limit=0", "limit=101", "offset=-1"):
        assert client.get(f"/api/v1/courses?{query}", headers=headers).status_code == 422
    assert client.get("/api/v1/courses/not-a-uuid", headers=headers).status_code == 422
