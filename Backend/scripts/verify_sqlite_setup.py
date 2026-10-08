"""Validate CLI migrations against a disposable on-disk database, never user data."""

import os
from contextlib import closing
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="setup-check-", dir=root) as directory:
        work = Path(directory).resolve()
        assert work.parent == root
        database = work / "acceptance.db"
        env = {key: value for key, value in os.environ.items()
               if not key.upper().startswith("EDUVANCE_")}
        env.update(EDUVANCE_DATABASE_URL=f"sqlite:///{database.as_posix()}",
                   EDUVANCE_DEBUG="false", EDUVANCE_ENVIRONMENT="test")

        def alembic(*args):
            subprocess.run([sys.executable, "-m", "alembic", *args],
                           cwd=root, env=env, check=True)

        alembic("upgrade", "head")
        alembic("current")
        alembic("check")
        with closing(sqlite3.connect(database)) as connection:
            assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0001",)
            tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            assert len(tables) == 17, tables
        alembic("downgrade", "base")
        with closing(sqlite3.connect(database)) as connection:
            tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            assert tables == [("alembic_version",)], tables
        alembic("upgrade", "head")
        alembic("check")
        print("PASS: fresh on-disk SQLite upgrade, schema check, rollback and re-upgrade")


if __name__ == "__main__":
    main()
