# Database setup

Run commands from the repository root with the project virtual environment.
Copy `Backend/.env.example` to `.env` if needed. `EDUVANCE_DATABASE_URL`
selects the database; the default is `Database/eduvance.db` (SQLite).

For a fresh database:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
.\.venv\Scripts\python.exe -m alembic check
```

Migration `0001` creates the 16 existing ORM tables plus Alembic's revision
table. Migrations are static snapshots; subsequent schema changes require
new revisions. Review generated revisions before applying them:

```powershell
.\.venv\Scripts\python.exe -m alembic revision --autogenerate -m "Describe schema change"
```

Use migrations for persistent databases instead of `init_db()` / `create_all()`.
An existing database created with `create_all()` needs a separate schema comparison
and adoption procedure; do not run this initial migration over its existing tables
or blindly stamp it as current. Existing data was not migrated during this session.

`alembic downgrade base` drops all application tables and their data. The test
suite exercises this only against a disposable in-memory database.

```powershell
.\.venv\Scripts\python.exe -m pytest Backend/tests/test_migrations.py -q -p no:cacheprovider
```

SQLite is validated. PostgreSQL needs its configured driver and live validation.
The initial revision preserves the existing portable String UUIDs, generic JSON,
and Python-side defaults; it does not add database-side defaults or new business
constraints. Raw SQL inserts must supply required values. Account authorization
and cross-course ownership validation remain application responsibilities.
