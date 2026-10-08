"""
Eduvance AI - Application Configuration (Pydantic Settings v2)

Loads environment variables from .env file with sensible defaults
for local SQLite development. Copy Backend/.env.example to the repository
root as .env and run commands from that root. Set EDUVANCE_DATABASE_URL
to select a database; process environment variables override .env values.

Reference: WBS 2.1 Section 3 (Technology Stack Selection)
Owner: Member 1 (Project Manager & Backend/Deployment Engineer)
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Central application configuration derived from environment variables."""

    # ── Project Metadata ──────────────────────────────────────────────
    PROJECT_NAME: str = "Eduvance AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # ── Database Configuration ────────────────────────────────────────
    # Default: SQLite for zero-setup local development
    # Production: postgresql+psycopg2://user:pass@host:5432/eduvance_db
    DATABASE_URL: str = "sqlite:///./Database/eduvance.db"

    # ── Local File Storage ────────────────────────────────────────────
    STORAGE_DIR: str = "./Backend/storage"
    MAX_UPLOAD_SIZE_MB: int = 50

    # ── Security & JWT Authentication ─────────────────────────────────
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── Platform Scope Limits (from WBS 1.2 Proposal) ─────────────────
    MAX_DOCUMENTS_PER_COURSE: int = 3
    MAX_PAGES_TOTAL: int = 50
    MAX_MODULES_PER_COURSE: int = 4
    MAX_LESSONS_PER_MODULE: int = 3
    PASSING_SCORE_PERCENTAGE: int = 70
    MAX_RETRY_COUNT: int = 2

    @property
    def storage_path(self) -> Path:
        """Return resolved absolute path to the storage directory."""
        return Path(self.STORAGE_DIR).resolve()

    model_config = {
        "env_prefix": "EDUVANCE_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Singleton instance used across the application
settings = Settings()
