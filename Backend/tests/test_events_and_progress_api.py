"""
Eduvance AI - Events & Progress REST API Integration Tests
WBS 4.1 - Endpoint Verification & Multi-User Isolation

Tests:
- POST /api/v1/events (authenticated event ingestion).
- GET /api/v1/events/course/{id} (event history).
- GET /api/v1/courses/{id}/progress (Contract 6 Progress report).
- GET /api/v1/courses/{id}/workflow (Workflow tasks status).
- POST /api/v1/courses/{id}/approve (Instructor course approval).
- Multi-user tenant isolation (401 unauthorized, 403 non-owner approval rejection).

Owner: Member 1 (Project Manager and Backend/Deployment Engineer)
"""

from pathlib import Path
from uuid import uuid4
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from Backend.core.config import Settings
from Backend.main import create_app
from Database.models.all_models import Course, Lesson, Module, User


@pytest.fixture
def api_client():
    """Sets up an in-memory SQLite database via Alembic migrations and two authenticated users."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    app_settings = Settings(_env_file=None, SECRET_KEY="test-only-workflow-key-" * 3)
    app = create_app(engine, app_settings)

    with TestClient(app) as client:
        # Register User A (Instructor) and User B (Learner)
        users = {}
        for role, name in [("INSTRUCTOR", "alice_inst"), ("LEARNER", "bob_learn")]:
            creds = {"email": f"{name}@example.com", "password": "secure-password-123"}
            reg = client.post("/api/v1/auth/register", json={**creds, "full_name": name})
            assert reg.status_code == 201
            # Update role directly in DB if INSTRUCTOR
            if role == "INSTRUCTOR":
                with Session(engine) as session:
                    db_user = session.query(User).filter(User.id == reg.json()["id"]).first()
                    db_user.role = "INSTRUCTOR"
                    session.commit()

            login = client.post("/api/v1/auth/login", json=creds)
            assert login.status_code == 200
            users[role] = {
                "id": reg.json()["id"],
                "headers": {"Authorization": f"Bearer {login.json()['access_token']}"},
            }

        yield client, engine, users

    engine.dispose()


def test_event_ingestion_api(api_client):
    """Verifies POST /api/v1/events records learner telemetry."""
    client, engine, users = api_client
    alice = users["INSTRUCTOR"]
    bob = users["LEARNER"]

    # 1. Alice creates a course
    c_res = client.post(
        "/api/v1/courses",
        headers=alice["headers"],
        json={"title": "Cloud Native Architecture", "domain": "DEVOPS"},
    )
    assert c_res.status_code == 201
    course_id = c_res.json()["id"]

    # 2. Bob ingests a VIDEO_WATCHED event
    event_payload = {
        "course_id": course_id,
        "event_type": "VIDEO_WATCHED",
        "payload": {"seconds_watched": 120, "total_duration": 150, "completed": True},
    }
    e_res = client.post("/api/v1/events", headers=bob["headers"], json=event_payload)
    assert e_res.status_code == 201
    event_data = e_res.json()
    assert event_data["event_type"] == "VIDEO_WATCHED"
    assert event_data["course_id"] == course_id

    # 3. Query events for course
    list_res = client.get(f"/api/v1/events/course/{course_id}", headers=bob["headers"])
    assert list_res.status_code == 200
    events = list_res.json()
    assert len(events) >= 1
    assert events[0]["event_type"] == "VIDEO_WATCHED"


def test_progress_evaluation_api(api_client):
    """Verifies GET /api/v1/courses/{id}/progress returns Contract 6 structure."""
    client, engine, users = api_client
    alice = users["INSTRUCTOR"]
    bob = users["LEARNER"]

    # Alice creates course
    c_res = client.post(
        "/api/v1/courses",
        headers=alice["headers"],
        json={"title": "Modern Cloud Computing", "domain": "CLOUD"},
    )
    course_id = c_res.json()["id"]

    # Bob queries progress
    p_res = client.get(f"/api/v1/courses/{course_id}/progress", headers=bob["headers"])
    assert p_res.status_code == 200
    progress = p_res.json()

    assert "overall_completion_percentage" in progress
    assert "concept_mastery_summary" in progress
    assert "recommendations" in progress
    assert progress["overall_completion_percentage"] == 0.0


def test_workflow_status_and_course_approval_api(api_client):
    """Verifies GET /api/v1/courses/{id}/workflow and POST /api/v1/courses/{id}/approve."""
    client, engine, users = api_client
    alice = users["INSTRUCTOR"]
    bob = users["LEARNER"]

    # 1. Alice creates course
    c_res = client.post(
        "/api/v1/courses",
        headers=alice["headers"],
        json={"title": "Enterprise Security", "domain": "CYBERSECURITY"},
    )
    course_id = c_res.json()["id"]

    # 2. Query initial workflow status
    w_res = client.get(f"/api/v1/courses/{course_id}/workflow", headers=alice["headers"])
    assert w_res.status_code == 200
    w_data = w_res.json()
    assert w_data["course_status"] == "DRAFT"

    # Set course to PENDING_APPROVAL in database to test approval endpoint
    with Session(engine) as session:
        course = session.query(Course).filter(Course.id == course_id).first()
        course.status = "PENDING_APPROVAL"
        session.commit()

    # 3. Bob (non-owner) attempts to approve -> 403 Forbidden
    bob_app_res = client.post(f"/api/v1/courses/{course_id}/approve", headers=bob["headers"])
    assert bob_app_res.status_code == 403

    # 4. Alice (owner) approves course -> 200 OK, transitions to ACTIVE
    alice_app_res = client.post(f"/api/v1/courses/{course_id}/approve", headers=alice["headers"])
    assert alice_app_res.status_code == 200
    assert alice_app_res.json()["status"] == "ACTIVE"

    # 5. Check workflow status is now 100%
    w_after = client.get(f"/api/v1/courses/{course_id}/workflow", headers=alice["headers"])
    assert w_after.status_code == 200
    assert w_after.json()["course_status"] == "ACTIVE"
    assert w_after.json()["progress_percentage"] == 100.0


def test_unauthenticated_requests_rejected(api_client):
    """Verifies endpoints reject missing authorization with 401."""
    client, engine, users = api_client
    dummy_id = str(uuid4())

    assert client.get(f"/api/v1/courses/{dummy_id}/progress").status_code == 401
    assert client.get(f"/api/v1/courses/{dummy_id}/workflow").status_code == 401
    assert client.post(f"/api/v1/courses/{dummy_id}/approve").status_code == 401
    assert client.post("/api/v1/events", json={}).status_code == 401
