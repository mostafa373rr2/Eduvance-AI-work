"""FastAPI entry point: run with `python -m uvicorn Backend.main:app`."""

from contextlib import asynccontextmanager
from pathlib import Path

from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from Backend.core.config import Settings, settings
from Backend.auth import auth_dependencies, auth_router
from Backend.courses import course_router
from Backend.documents import document_router
from Backend.services.storage_service import StorageService
from Database.models.all_models import Base
from Database.session import engine


def create_app(database_engine: Engine | None = None, app_settings: Settings | None = None,
               storage: StorageService | None = None) -> FastAPI:
    """Build the application; injected engines remain owned by their caller."""
    db_engine = database_engine if database_engine is not None else engine
    app_config = app_settings if app_settings is not None else settings
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    expected_heads = set(ScriptDirectory.from_config(config).get_heads())

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        # Migrations are an explicit deployment step, never a startup mutation.
        try:
            yield
        finally:
            if database_engine is None:
                db_engine.dispose()

    application = FastAPI(title=app_config.PROJECT_NAME, lifespan=lifespan)
    dependencies = auth_dependencies(sessionmaker(bind=db_engine), app_config)
    application.include_router(auth_router(dependencies, app_config),
                               prefix=app_config.API_V1_STR)
    application.include_router(course_router(dependencies), prefix=app_config.API_V1_STR)
    application.include_router(document_router(dependencies, storage if storage is not None
                               else StorageService(app_config.STORAGE_DIR)),
                               prefix=app_config.API_V1_STR)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request, error):
        # Pydantic errors include rejected inputs by default, including passwords.
        return JSONResponse(status_code=422, content={"detail": [
            {key: item[key] for key in ("loc", "msg", "type")}
            for item in error.errors()
        ]})

    @application.get("/health/live", tags=["Health"])
    def liveness():
        return {"status": "alive"}

    @application.get("/health/ready", tags=["Health"], responses={503: {"description": "Database not ready"}})
    def readiness():
        try:
            with db_engine.connect() as connection:
                actual_heads = set(MigrationContext.configure(connection).get_current_heads())
                if actual_heads != expected_heads:
                    return JSONResponse(status_code=503, content={"status": "not_ready"})
                # Verify mapped tables and columns are readable without fetching rows.
                # A stamped revision alone does not prove the schema exists.
                for table in Base.metadata.sorted_tables:
                    connection.execute(select(table).limit(0)).close()
        except SQLAlchemyError:
            # Do not expose URLs, SQL text or driver errors in a public health response.
            return JSONResponse(status_code=503, content={"status": "not_ready"})
        return {"status": "ready"}

    return application


app = create_app()
