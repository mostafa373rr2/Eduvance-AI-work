"""Exercise migrations without touching the configured application database."""

from io import StringIO
from pathlib import Path

import pytest
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError

from Database.models.all_models import Base, Course, User


@pytest.fixture
def migrated_database():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")
        connection.commit()
        config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        yield config, connection
    engine.dispose()


def test_schema_round_trip_and_repeated_upgrade(migrated_database):
    config, connection = migrated_database
    expected = set(Base.metadata.tables) | {"alembic_version"}
    assert set(inspect(connection).get_table_names()) == expected
    assert MigrationContext.configure(connection).get_current_revision() == "0001"
    assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
    connection.execute(User.__table__.insert().values(
        id="user-a", email="test@example.invalid", password_hash="test-only",
        full_name="Migration Test"))
    connection.commit()
    command.upgrade(config, "head")
    assert connection.scalar(select(User.id)) == "user-a"
    connection.commit()
    command.downgrade(config, "base")
    assert set(inspect(connection).get_table_names()) == {"alembic_version"}
    assert MigrationContext.configure(connection).get_current_revision() is None
    connection.commit()
    command.upgrade(config, "head")
    assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []


def test_migrated_constraints_and_cascade(migrated_database):
    _, connection = migrated_database
    users, courses = User.__table__, Course.__table__
    connection.execute(users.insert().values(id="owner", email="owner@example.invalid",
                                             password_hash="test", full_name="Owner"))
    connection.commit()
    with pytest.raises(IntegrityError):
        connection.execute(users.insert().values(email="owner@example.invalid",
                                                 password_hash="test", full_name="Duplicate"))
    connection.rollback()
    with pytest.raises(IntegrityError):
        connection.execute(courses.insert().values(user_id="missing", title="Test", domain="Test"))
    connection.rollback()
    connection.execute(courses.insert().values(user_id="owner", title="Test", domain="Test"))
    connection.commit()
    connection.execute(users.delete().where(users.c.id == "owner"))
    connection.commit()
    assert connection.scalar(select(courses.c.id)) is None


def test_offline_sql_generation():
    output = StringIO()
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"),
                    output_buffer=output)
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    assert "CREATE TABLE users" in sql
    assert "CREATE TABLE workflow_tasks" in sql
    assert "0001" in sql
