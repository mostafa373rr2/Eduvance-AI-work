"""Verify that the shipped environment template matches the settings loader."""

import os
from pathlib import Path

import pytest

from Backend.core.config import Settings


EXAMPLE = Path(__file__).resolve().parents[1] / ".env.example"


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch):
    for name in list(os.environ):
        if name.upper().startswith("EDUVANCE_"):
            monkeypatch.delenv(name)


def test_documented_example_loads():
    # Distinct defaults expose silently ignored entries in the example.
    class DistinctDefaults(Settings):
        PROJECT_NAME: str = "Template was not loaded"
        DATABASE_URL: str = "sqlite:///:memory:"
        DEBUG: bool = False
        MAX_UPLOAD_SIZE_MB: int = 1

    settings = DistinctDefaults(_env_file=EXAMPLE)
    assert settings.PROJECT_NAME == "Eduvance AI"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is True
    assert settings.DATABASE_URL == "sqlite:///./Database/eduvance.db"
    assert settings.STORAGE_DIR == "./Backend/storage"
    assert settings.MAX_UPLOAD_SIZE_MB == 50
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 1440


def test_environment_overrides_example(monkeypatch):
    monkeypatch.setenv("EDUVANCE_DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("EDUVANCE_DEBUG", "false")
    monkeypatch.setenv("EDUVANCE_MAX_UPLOAD_SIZE_MB", "12")
    settings = Settings(_env_file=EXAMPLE)
    assert settings.DATABASE_URL == "sqlite:///:memory:"
    assert settings.DEBUG is False
    assert settings.MAX_UPLOAD_SIZE_MB == 12


def test_defaults_without_dotenv():
    settings = Settings(_env_file=None)
    assert settings.MAX_DOCUMENTS_PER_COURSE == 3
    assert settings.MAX_PAGES_TOTAL == 50
    assert settings.MAX_RETRY_COUNT == 2
