"""Source downloads using disposable files and a migrated in-memory database."""

import asyncio
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from Backend.core.config import Settings
from Backend.main import create_app
from Backend.services.storage_service import StorageService
from Database.models.all_models import Course, Document, User


@pytest.fixture
def documents():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    settings = Settings(_env_file=None, SECRET_KEY="test-only-document-signing-key-" * 3)
    with tempfile.TemporaryDirectory(prefix="document-test-", dir=Path.cwd()) as folder:
        assert Path(folder).resolve().parent == Path.cwd().resolve()
        storage = StorageService(str(Path(folder) / "storage"))
        records = []
        with Session(engine) as session:
            for name in ("alice", "bob"):
                user = User(email=f"{name}@example.com", password_hash="unused-test-hash", full_name=name)
                session.add(user)
                session.flush()
                course = Course(user_id=user.id, title=name, domain="test")
                session.add(course)
                session.flush()
                content = b"%PDF-1.4\n" + name.encode() * 20000
                path = asyncio.run(storage.save_upload(course.id, "source.pdf", content))
                document = Document(course_id=course.id, filename="source.pdf", file_path=str(path),
                                    file_hash_sha256=storage.compute_sha256(content), page_count=1,
                                    file_size_bytes=len(content))
                session.add(document)
                session.flush()
                now = datetime.now(timezone.utc)
                token = jwt.encode({"sub": user.id, "iat": now, "exp": now + timedelta(minutes=5),
                                    "iss": "eduvance", "aud": "eduvance-api", "token_type": "access"},
                                   settings.SECRET_KEY, algorithm="HS256")
                records.append({"course": course.id, "document": document.id, "path": path,
                                "content": content, "headers": {"Authorization": f"Bearer {token}"}})
            session.commit()
        with TestClient(create_app(engine, settings, storage)) as client:
            yield client, engine, storage, records
    engine.dispose()


def url(record):
    return f"/api/v1/courses/{record['course']}/documents/{record['document']}/download"


def test_owner_download_absolute_and_relative_metadata(documents):
    client, engine, storage, records = documents
    record = records[0]
    for stored_path in (str(record["path"]), record["path"].relative_to(storage.base_dir).as_posix()):
        with Session(engine) as session:
            session.get(Document, record["document"]).file_path = stored_path
            session.commit()
        response = client.get(url(record), headers=record["headers"])
        assert response.status_code == 200
        assert response.content == record["content"]
        assert response.headers["content-type"] == "application/pdf"
        assert response.headers["content-disposition"] == f'attachment; filename="{record["document"]}.pdf"'
        assert response.headers["cache-control"] == "private, no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert int(response.headers["content-length"]) == len(record["content"])


def test_unauthorized_requests_never_lookup_files(documents):
    client, _, storage, records = documents
    alice, bob = records
    with patch.object(storage, "get_document_path", side_effect=AssertionError("Unexpected file lookup")):
        assert client.get(url(alice)).status_code == 401
        assert client.get(url(alice), headers={"Authorization": "Bearer bad"}).status_code == 401
        assert client.get(url(alice), headers=bob["headers"]).status_code == 404
        assert client.get(url(bob), headers=alice["headers"]).status_code == 404
        mixed = {**alice, "document": bob["document"]}
        assert client.get(url(mixed), headers=alice["headers"]).status_code == 404
        assert client.get(url({**alice, "document": str(uuid4())}), headers=alice["headers"]).status_code == 404


def test_missing_and_inaccessible_files_are_sanitized(documents):
    client, _, storage, records = documents
    alice = records[0]
    with patch.object(Path, "open", side_effect=PermissionError("private filesystem detail")):
        response = client.get(url(alice), headers=alice["headers"])
        assert response.status_code == 404
        assert response.json() == {"detail": "Document not found"}
    alice["path"].unlink()
    response = client.get(url(alice), headers=alice["headers"])
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}


def test_metadata_cannot_escape_course_or_storage(documents):
    client, engine, storage, records = documents
    alice, bob = records
    outside = storage.base_dir.parent / "outside.pdf"
    outside.write_bytes(b"private outside data")
    invalid_paths = [str(bob["path"]), bob["path"].relative_to(storage.base_dir).as_posix(),
                     str(outside), "../outside.pdf", "..\\outside.pdf",
                     str(alice["path"].parent)]
    for stored_path in invalid_paths:
        with Session(engine) as session:
            session.get(Document, alice["document"]).file_path = stored_path
            session.commit()
        response = client.get(url(alice), headers=alice["headers"])
        assert response.status_code == 404
        assert response.json() == {"detail": "Document not found"}


def test_metadata_listing_is_public_and_download_link_works(documents):
    client, engine, storage, records = documents
    for record in records:
        with Session(engine) as session:
            session.get(Document, record["document"]).filename = "C:\\private\\source.pdf"
            session.commit()
        with patch.object(storage, "get_document_path", side_effect=AssertionError("Listing must not read files")):
            response = client.get(f"/api/v1/courses/{record['course']}/documents", headers=record["headers"])
        assert response.status_code == 200
        assert response.headers["cache-control"] == "private, no-store"
        items = response.json()
        assert len(items) == 1
        assert set(items[0]) == {"id", "course_id", "filename", "page_count", "file_size_bytes",
                                 "upload_status", "created_at", "download_url"}
        assert items[0]["id"] == record["document"]
        assert items[0]["course_id"] == record["course"]
        assert items[0]["filename"] == "source.pdf"
        assert items[0]["page_count"] == 1
        assert items[0]["file_size_bytes"] == len(record["content"])
        assert items[0]["upload_status"] == "UPLOADED"
        assert items[0]["download_url"] == url(record)
        assert str(storage.base_dir) not in response.text
        assert "private" not in response.text
        download = client.get(items[0]["download_url"], headers=record["headers"])
        assert download.status_code == 200
        assert download.content == record["content"]


def test_metadata_listing_denies_foreign_and_unknown_courses(documents):
    client, _, storage, records = documents
    alice, bob = records
    endpoint = f"/api/v1/courses/{alice['course']}/documents"
    with patch.object(storage, "get_document_path", side_effect=AssertionError("Unexpected lookup")):
        assert client.get(endpoint).status_code == 401
        assert client.get(endpoint, headers={"Authorization": "Bearer invalid"}).status_code == 401
        foreign = client.get(endpoint, headers=bob["headers"])
        missing = client.get(f"/api/v1/courses/{uuid4()}/documents", headers=bob["headers"])
        assert foreign.status_code == missing.status_code == 404
        assert foreign.json() == missing.json() == {"detail": "Course not found"}


def test_metadata_listing_empty_pagination_and_missing_file(documents):
    client, engine, _, records = documents
    record = records[0]
    endpoint = f"/api/v1/courses/{record['course']}/documents"
    headers = record["headers"]
    record["path"].unlink()
    # Metadata remains visible when a stored file needs recovery.
    assert len(client.get(endpoint, headers=headers).json()) == 1
    with Session(engine) as session:
        owner_id = session.get(Course, record["course"]).user_id
        empty_course = Course(user_id=owner_id, title="Empty", domain="Test")
        session.add(empty_course)
        for index in range(2):
            session.add(Document(course_id=record["course"], filename=f"extra{index}.pdf",
                                 file_path="missing.pdf", file_hash_sha256="0" * 64,
                                 page_count=1, file_size_bytes=10))
        session.commit()
        empty_id = empty_course.id
    response = client.get(f"/api/v1/courses/{empty_id}/documents", headers=headers)
    assert response.status_code == 200
    assert response.json() == []
    items = client.get(endpoint, headers=headers).json()
    assert len(items) == 3
    pages = [client.get(f"{endpoint}?limit=1&offset={index}", headers=headers).json()[0]
             for index in range(3)]
    assert pages == items
    assert client.get(f"{endpoint}?offset=3", headers=headers).json() == []
    for query in ("limit=0", "limit=101", "offset=-1"):
        assert client.get(f"{endpoint}?{query}", headers=headers).status_code == 422
    assert client.get("/api/v1/courses/not-a-uuid/documents", headers=headers).status_code == 422
