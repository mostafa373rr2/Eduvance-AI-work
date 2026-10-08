"""Owner-authorized metadata and downloads for existing source documents."""

import os
from datetime import datetime
from pathlib import PureWindowsPath
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.background import BackgroundTask

from Backend.auth import AuthDependencies
from Backend.courses import owned_course
from Backend.services.storage_service import StorageService
from Database.models.all_models import Document, User


class DocumentMetadata(BaseModel):
    id: str
    course_id: str
    filename: str
    page_count: int
    file_size_bytes: int
    upload_status: str
    created_at: datetime
    download_url: str


def document_router(dependencies: AuthDependencies, storage: StorageService) -> APIRouter:
    router = APIRouter(prefix="/courses", tags=["Source documents"])

    @router.get("/{course_id}/documents", response_model=list[DocumentMetadata])
    def list_documents(course_id: UUID, request: Request, response: Response,
                       limit: int = Query(default=20, ge=1, le=100),
                       offset: int = Query(default=0, ge=0),
                       user: User = Depends(dependencies.current_user),
                       session: Session = Depends(dependencies.database)):
        owned_course(session, course_id, user.id)
        documents = session.scalars(select(Document).where(Document.course_id == str(course_id))
                                    .order_by(Document.created_at, Document.id)
                                    .offset(offset).limit(limit)).all()
        response.headers["Cache-Control"] = "private, no-store"
        # An explicit public schema excludes storage paths and internal hashes.
        return [DocumentMetadata(
            id=document.id, course_id=document.course_id,
            filename=PureWindowsPath(document.filename).name or f"{document.id}.pdf",
            page_count=document.page_count, file_size_bytes=document.file_size_bytes,
            upload_status=document.upload_status, created_at=document.created_at,
            download_url=request.url_for("download_source_document", course_id=document.course_id,
                                         document_id=document.id).path,
        ) for document in documents]

    @router.get("/{course_id}/documents/{document_id}/download",
                name="download_source_document",
                response_class=StreamingResponse,
                responses={200: {"content": {"application/pdf": {}}}})
    def download(course_id: UUID, document_id: UUID,
                 user: User = Depends(dependencies.current_user),
                 session: Session = Depends(dependencies.database)):
        # Authorization precedes metadata and filesystem access.
        owned_course(session, course_id, user.id)
        document = session.scalar(select(Document).where(
            Document.id == str(document_id), Document.course_id == str(course_id)))
        if document is None:
            raise HTTPException(404, "Document not found")
        try:
            path = storage.get_document_path(str(course_id), document.file_path)
            if path is None:
                raise HTTPException(404, "Document not found")
            # Open before sending response headers so missing/inaccessible files
            # have a controlled response; stream bounded chunks from this handle.
            handle = path.open("rb")
        except (OSError, ValueError):
            raise HTTPException(404, "Document not found") from None

        def chunks():
            try:
                while chunk := handle.read(64 * 1024):
                    yield chunk
            finally:
                handle.close()

        try:
            size = os.fstat(handle.fileno()).st_size
        except OSError:
            handle.close()
            raise HTTPException(404, "Document not found") from None
        return StreamingResponse(chunks(), media_type="application/pdf", headers={
            "Content-Disposition": f'attachment; filename="{document_id}.pdf"',
            "Content-Length": str(size),
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        }, background=BackgroundTask(handle.close))

    return router
