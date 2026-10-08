"""Migration entry point using the application's configured database."""

from alembic import context

from Backend.core.config import settings
from Database.models.all_models import Base
from Database.session import engine


def run(connection):
    context.configure(connection=connection, target_metadata=Base.metadata,
                      compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=settings.DATABASE_URL, target_metadata=Base.metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
else:
    # Tests and embedding callers may supply a disposable connection.
    connection = context.config.attributes.get("connection")
    if connection is not None:
        run(connection)
    else:
        with engine.connect() as connection:
            run(connection)
