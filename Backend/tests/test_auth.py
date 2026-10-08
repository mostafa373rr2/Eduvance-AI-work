"""Account integration tests use a migrated, disposable SQLite database."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from Backend.core.config import Settings
from Backend.main import create_app
from Database.models.all_models import User


PASSWORD = "a-valid-test-password"
ACCOUNT = {"email": "learner@example.com", "password": PASSWORD, "full_name": "Learner"}


@pytest.fixture
def account_app():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    settings = Settings(_env_file=None, SECRET_KEY="test-only-signing-key-" * 3)
    with TestClient(create_app(engine, settings)) as client:
        yield client, engine, settings
    engine.dispose()


def test_registration_login_and_current_user(account_app):
    client, engine, _ = account_app
    response = client.post("/api/v1/auth/register", json={**ACCOUNT, "email": "Learner@EXAMPLE.com"})
    assert response.status_code == 201
    user = response.json()
    assert user["email"] == ACCOUNT["email"]
    assert user["role"] == "LEARNER"
    assert "password" not in response.text
    with Session(engine) as session:
        stored = session.scalar(select(User))
        assert stored.password_hash != PASSWORD
        assert bcrypt.checkpw(PASSWORD.encode(), stored.password_hash.encode())
    response = client.post("/api/v1/auth/login", json={"email": ACCOUNT["email"], "password": PASSWORD})
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    token = response.json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == user
    # A token stops authenticating when its account no longer exists.
    with engine.begin() as connection:
        connection.execute(User.__table__.delete())
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_duplicate_normalized_email(account_app):
    client, _, _ = account_app
    assert client.post("/api/v1/auth/register", json=ACCOUNT).status_code == 201
    assert client.post("/api/v1/auth/register", json={**ACCOUNT, "email": "LEARNER@example.com"}).status_code == 409


def test_failed_logins_have_same_response(account_app):
    client, _, _ = account_app
    client.post("/api/v1/auth/register", json=ACCOUNT)
    responses = [client.post("/api/v1/auth/login", json={"email": email, "password": "wrong-test-password"})
                 for email in (ACCOUNT["email"], "absent@example.com")]
    assert [r.status_code for r in responses] == [401, 401]
    assert responses[0].json() == responses[1].json()
    assert responses[0].headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("change", [{"password": "too-short"}, {"password": "x" * 73},
                                   {"password": "é" * 37}, {"email": "not-an-email"},
                                   {"full_name": " "}, {"role": "ADMIN"}])
def test_registration_validation_and_no_secret_echo(account_app, change):
    client, _, _ = account_app
    payload = {**ACCOUNT, **change}
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert payload["password"] not in response.text
    assert all("input" not in error for error in response.json()["detail"])


@pytest.mark.parametrize("mode", ["missing", "garbage", "expired", "wrong-key", "no-exp", "wrong-audience", "wrong-type"])
def test_invalid_tokens(account_app, mode):
    client, _, config = account_app
    user_id = client.post("/api/v1/auth/register", json=ACCOUNT).json()["id"]
    now = datetime.now(timezone.utc)
    claims = {"sub": user_id, "iat": now, "exp": now + timedelta(minutes=5),
              "aud": "eduvance-api", "iss": "eduvance", "token_type": "access"}
    if mode == "expired":
        claims["exp"] = now - timedelta(minutes=1)
    if mode == "no-exp":
        del claims["exp"]
    if mode == "wrong-audience":
        claims["aud"] = "different-service"
    if mode == "wrong-type":
        claims["token_type"] = "refresh"
    key = "different-signing-key-" * 3 if mode == "wrong-key" else config.SECRET_KEY
    token = "garbage" if mode == "garbage" else jwt.encode(claims, key, algorithm="HS256")
    headers = {} if mode == "missing" else {"Authorization": f"Bearer {token}"}
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


@pytest.mark.parametrize("key", ["", "short", "eduvance-secret-key-change-in-production-for-security"])
def test_unconfigured_signing_key_disables_auth(account_app, key):
    client, _, config = account_app
    config.SECRET_KEY = key
    assert client.post("/api/v1/auth/register", json=ACCOUNT).status_code == 503
    assert client.post("/api/v1/auth/login", json={"email": ACCOUNT["email"], "password": PASSWORD}).status_code == 503
    assert client.get("/api/v1/auth/me").status_code == 503
    assert client.get("/health/live").status_code == 200
