"""Application lifecycle/readiness checks against disposable SQLite databases."""

from pathlib import Path
from unittest.mock import patch

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import StaticPool

from Backend.main import create_app


@pytest.fixture
def database_engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    yield engine
    engine.dispose()


def migrate(engine):
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def test_uninitialized_database_starts_but_is_not_ready(database_engine):
    with TestClient(create_app(database_engine)) as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        response = client.get("/health/ready")
        assert response.status_code == 503
        assert response.json() == {"status": "not_ready"}
        assert inspect(database_engine).get_table_names() == []
        migrate(database_engine)
        assert client.get("/health/ready").status_code == 200


def test_migrated_database_startup_and_openapi(database_engine):
    migrate(database_engine)
    with TestClient(create_app(database_engine)) as client:
        response = client.get("/health/ready")
        assert response.status_code == 200
        assert response.json() == {"status": "ready"}
        assert client.get("/health/live").status_code == 200
        schema = client.get("/openapi.json").json()
        assert "/health/ready" in schema["paths"]
        assert client.get("/docs").status_code == 200


@pytest.mark.parametrize("damage", ["DELETE FROM alembic_version",
                                   "UPDATE alembic_version SET version_num = 'unknown'",
                                   "DROP TABLE users"])
def test_missing_revision_or_table_is_not_ready(database_engine, damage):
    migrate(database_engine)
    with database_engine.begin() as connection:
        connection.exec_driver_sql(damage)
    with TestClient(create_app(database_engine)) as client:
        assert client.get("/health/ready").status_code == 503
        assert client.get("/health/live").status_code == 200


def test_connection_failure_is_sanitized_and_recovers(database_engine):
    migrate(database_engine)
    with TestClient(create_app(database_engine)) as client:
        with patch.object(database_engine, "connect", side_effect=OperationalError(
                "private SQL", {}, Exception("private connection credentials"))):
            response = client.get("/health/ready")
            assert response.status_code == 503
            assert response.json() == {"status": "not_ready"}
            assert client.get("/health/live").status_code == 200
        assert client.get("/health/ready").status_code == 200
