"""Regression checks for storage confinement; all files are disposable."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from Backend.services.storage_service import StorageService


@pytest.fixture
def storage():
    # Keep test artifacts inside the workspace, including on Windows.
    with tempfile.TemporaryDirectory(prefix="storage-test-", dir=Path.cwd()) as directory:
        yield StorageService(str(Path(directory) / "storage"))


def test_normal_save_lookup_and_course_deletion(storage):
    upload = asyncio.run(storage.save_upload("course-a", "source.pdf", b"example"))
    asset = storage.save_lesson_asset("course-a", "lesson-a", "slide.png", b"image")
    other = asyncio.run(storage.save_upload("course-b", "keep.pdf", b"keep"))
    assert upload.read_bytes() == b"example"
    assert asset.read_bytes() == b"image"
    assert storage.get_file_path("uploads/course-a/source.pdf") == upload
    assert storage.get_file_path("uploads/course-a/missing.pdf") is None
    assert storage.get_file_path("uploads/course-a") is None
    storage.delete_course_files("course-a")
    assert not upload.exists()
    assert not asset.exists()
    assert other.read_bytes() == b"keep"


@pytest.mark.parametrize("value", ["", ".", "..", "../other", "..\\other", "/absolute",
                                  "C:\\absolute", "C:relative", "a/b", "a\\b",
                                  "file:stream", "NUL", "CON.pdf", "trailing.", "trailing "])
def test_reject_invalid_identifiers_before_deletion(storage, value):
    sentinel = asyncio.run(storage.save_upload("keep", "source.pdf", b"keep"))
    with pytest.raises(ValueError):
        storage.get_upload_dir(value)
    with pytest.raises(ValueError):
        storage.get_lesson_dir("course-a", value)
    with pytest.raises(ValueError):
        storage.delete_course_files(value)
    assert sentinel.read_bytes() == b"keep"


@pytest.mark.parametrize("filename", ["../../escaped.pdf", "..\\..\\escaped.pdf",
                                     "/escaped.pdf", "C:\\escaped.pdf", "NUL.pdf"])
def test_reject_upload_and_asset_filename_paths(storage, filename):
    with pytest.raises(ValueError):
        asyncio.run(storage.save_upload("course-a", filename, b"test"))
    with pytest.raises(ValueError):
        storage.save_lesson_asset("course-a", "lesson-a", filename, b"test")


@pytest.mark.parametrize("path", ["../outside.pdf", "uploads/../outside.pdf",
                                 "..\\outside.pdf", "/outside.pdf", "C:\\outside.pdf",
                                 "C:outside.pdf", "uploads//file.pdf", "uploads/a:stream"])
def test_reject_lookup_paths(storage, path):
    with pytest.raises(ValueError):
        storage.get_file_path(path)


def test_symlink_escape_is_rejected(storage):
    outside = storage.base_dir.parent / "outside"
    outside.mkdir()
    sentinel = outside / "keep.pdf"
    sentinel.write_bytes(b"keep")
    link = storage.base_dir / "uploads" / "linked"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"Symlink creation unavailable: {error}")
    with pytest.raises(ValueError):
        storage.get_upload_dir("linked")
    with pytest.raises(ValueError):
        storage.get_file_path("uploads/linked/keep.pdf")
    with pytest.raises(ValueError):
        storage.delete_course_files("linked")
    assert sentinel.read_bytes() == b"keep"
