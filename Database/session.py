"""
Eduvance AI - Database Session & Engine Configuration

Provides the SQLAlchemy engine, declarative base, and session factory.
Supports SQLite (local dev) and PostgreSQL (production) via DATABASE_URL.

Reference: WBS 2.1 Section 3 & 7 (Technology Stack & Table Specifications)
Owner: Member 1 (Project Manager & Backend/Deployment Engineer)
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from Backend.core.config import settings


# ── Engine Configuration ──────────────────────────────────────────────
# SQLite requires connect_args for multi-threaded FastAPI access.
# PostgreSQL uses standard connection pooling without this argument.
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = {}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  # Account queries contain password hashes; never echo SQL parameters.
    hide_parameters=True,
    **_engine_kwargs,
)


# ── Enable Foreign Key Enforcement for SQLite ─────────────────────────
# SQLite does not enforce foreign keys by default; this listener ensures
# ON DELETE CASCADE and referential integrity work correctly.
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# ── Declarative Base ──────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Root base class for all Eduvance AI database models."""
    pass


# ── Session Factory ───────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db():
    """
    FastAPI dependency that provides a database session per request.

    Usage in routers:
        from Database.session import get_db
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables defined in the metadata.
    Legacy helper for disposable databases only. For persistent databases,
    run `python -m alembic upgrade head` from the repository root instead.

    NOTE: Import all model modules BEFORE calling this function
    so that SQLAlchemy registers their table definitions on Base.metadata.
    """
    import Database.models.all_models  # noqa: F401 — force model registration
    Base.metadata.create_all(bind=engine)
