"""
Eduvance AI - Local File Storage Service

Manages structured file storage for uploaded PDFs, generated slides,
audio narration, subtitle tracks, and assembled video assets.
Confines paths to their course and lesson directories. Callers must
separately authorize the user's access to the requested course.

Reference: WBS 2.1 Section 5 (Persistence & Storage Layer)
Owner: Member 1 (Project Manager & Backend/Deployment Engineer)
"""

import hashlib
import shutil
from pathlib import Path, PureWindowsPath
from typing import Optional

from Backend.core.config import settings


# Allowed file extensions by category
ALLOWED_EXTENSIONS = {
    "upload": {".pdf"},
    "slide": {".png", ".jpg", ".jpeg"},
    "audio": {".mp3", ".wav"},
    "subtitle": {".vtt", ".srt"},
    "video": {".mp4"},
}

ALL_ALLOWED = set().union(*ALLOWED_EXTENSIONS.values())


class StorageService:
    """Manages local file system storage with course/lesson isolation."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.STORAGE_DIR).resolve()
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create top-level storage subdirectories if they don't exist."""
        for subdir in ("uploads", "courses", "temp"):
            self._resolve_within(self.base_dir, subdir).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _validate_component(value: str) -> str:
        """Accept one portable directory or file name, never a path."""
        if (
            not isinstance(value, str)
            or not value
            or value in {".", ".."}
            or any(c in value for c in '/\\:<>"|?*')
            or any(ord(c) < 32 for c in value)
            or value.endswith((".", " "))
            or value.split(".", 1)[0].upper()
            in {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$",
                *(f"COM{i}" for i in range(1, 10)),
                *(f"LPT{i}" for i in range(1, 10))}
        ):
            raise ValueError("Expected a single safe path component")
        return value

    @staticmethod
    def _resolve_within(root: Path, *parts: str) -> Path:
        """Check the resolved destination, including existing symlinks."""
        target = root.joinpath(*parts).resolve()
        if target == root or not target.is_relative_to(root):
            raise ValueError("Path escapes its storage directory")
        return target

    def _course_dir(self, category: str, course_id: str) -> Path:
        self._validate_component(course_id)
        root = self._resolve_within(self.base_dir, category)
        return self._resolve_within(root, course_id)

    # ── Path Builders ─────────────────────────────────────────────────

    def get_upload_dir(self, course_id: str) -> Path:
        """Return (and create) the upload directory for a specific course."""
        path = self._course_dir("uploads", course_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_lesson_dir(self, course_id: str, lesson_id: str) -> Path:
        """Return (and create) the asset directory for a specific lesson."""
        self._validate_component(lesson_id)
        course_dir = self._course_dir("courses", course_id)
        lessons_dir = self._resolve_within(course_dir, "lessons")
        path = self._resolve_within(lessons_dir, lesson_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def get_temp_dir(self) -> Path:
        """Return the temporary processing directory."""
        return self._resolve_within(self.base_dir, "temp")

    # ── File Operations ───────────────────────────────────────────────

    def validate_extension(self, filename: str, category: str = "upload") -> bool:
        """Check whether the file extension is allowed for the given category."""
        ext = Path(filename).suffix.lower()
        allowed = ALLOWED_EXTENSIONS.get(category, ALL_ALLOWED)
        return ext in allowed

    def validate_file_size(self, file_size_bytes: int) -> bool:
        """Check whether the file size is within the configured limit."""
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        return file_size_bytes <= max_bytes

    async def save_upload(self, course_id: str, filename: str, content: bytes) -> Path:
        """
        Save an uploaded file to the course upload directory.

        Returns the absolute path to the saved file.
        Raises ValueError if the extension is not allowed or file is too large.
        """
        if not self.validate_extension(filename, "upload"):
            raise ValueError(
                f"File type not allowed: '{Path(filename).suffix}'. "
                f"Allowed: {ALLOWED_EXTENSIONS['upload']}"
            )
        if not self.validate_file_size(len(content)):
            raise ValueError(
                f"File size ({len(content)} bytes) exceeds limit "
                f"({settings.MAX_UPLOAD_SIZE_MB} MB)."
            )

        self._validate_component(filename)
        upload_dir = self.get_upload_dir(course_id)
        file_path = self._resolve_within(upload_dir, filename)
        file_path.write_bytes(content)
        return file_path

    def save_lesson_asset(
        self,
        course_id: str,
        lesson_id: str,
        filename: str,
        content: bytes,
    ) -> Path:
        """
        Save a generated asset (slide, audio, video, subtitle) to the
        lesson directory.

        Returns the absolute path to the saved file.
        """
        ext = Path(filename).suffix.lower()
        if ext not in ALL_ALLOWED:
            raise ValueError(
                f"Asset type not allowed: '{ext}'. Allowed: {ALL_ALLOWED}"
            )

        self._validate_component(filename)
        lesson_dir = self.get_lesson_dir(course_id, lesson_id)
        file_path = self._resolve_within(lesson_dir, filename)
        file_path.write_bytes(content)
        return file_path

    @staticmethod
    def compute_sha256(content: bytes) -> str:
        """Compute SHA-256 hash of file content for integrity verification."""
        return hashlib.sha256(content).hexdigest()

    def delete_course_files(self, course_id: str) -> None:
        """Remove all stored files for a course (uploads + generated assets)."""
        # Validate both destinations before removing either directory.
        targets = [self._course_dir(subdir, course_id) for subdir in ("uploads", "courses")]
        for target in targets:
            if target.exists():
                shutil.rmtree(target)

    def get_file_path(self, relative_path: str) -> Optional[Path]:
        """
        Resolve a relative storage path to an absolute path.
        Returns None if the file does not exist.
        """
        if not isinstance(relative_path, str) or not relative_path:
            raise ValueError("Expected a relative file path")
        windows_path = PureWindowsPath(relative_path)
        if windows_path.drive or windows_path.root or Path(relative_path).is_absolute():
            raise ValueError("Expected a relative file path")
        parts = relative_path.replace("\\", "/").split("/")
        for part in parts:
            self._validate_component(part)
        full_path = self.base_dir
        for part in parts:
            full_path = self._resolve_within(full_path, part)
        return full_path if full_path.is_file() else None

    def get_document_path(self, course_id: str, stored_path: str) -> Optional[Path]:
        """Resolve metadata paths only within this course's upload directory.

        Accept root-relative paths or local absolute paths returned by save_upload.
        This performs no directory creation; callers must first authorize the course.
        """
        path = Path(stored_path)
        if path.is_absolute():
            path = path.relative_to(self.base_dir)
        resolved = self.get_file_path(str(path))
        if resolved is None:
            return None
        if resolved.parent != self._course_dir("uploads", course_id):
            raise ValueError("Document is outside its course upload directory")
        if resolved.suffix.lower() != ".pdf":
            raise ValueError("Document is not a PDF path")
        return resolved


# Singleton instance
storage_service = StorageService()
