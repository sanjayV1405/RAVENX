import os
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.document import DocumentResponse
from app.schemas.extraction import DocumentUploadResponse
from app.services.document_service import DocumentService
from app.core.config import settings

router = APIRouter()


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Uploads a document (PDF, DOCX, PPTX).
    Enforces maximum size of 25MB and format validation.
    Detects duplicates via cryptographic SHA-256 hash.
    Original file remains strictly immutable.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file payload is empty."
        )

    doc, is_duplicate = await DocumentService.upload_document(
        db=db,
        filename=file.filename or "unnamed_document",
        file_bytes=file_bytes
    )

    resp_dict = {
        "id": doc.id,
        "filename": doc.filename,
        "file_extension": doc.file_extension,
        "file_size_bytes": doc.file_size_bytes,
        "mime_type": doc.mime_type,
        "storage_path": doc.storage_path,
        "checksum": doc.checksum,
        "page_count": doc.page_count,
        "status": doc.status,
        "is_duplicate": is_duplicate,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }
    return DocumentUploadResponse(**resp_dict)


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Retrieves list of recently uploaded documents."""
    return DocumentService.list_documents(db=db, skip=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves details of a specific document."""
    return DocumentService.get_document(db=db, document_id=document_id)


@router.get("/{document_id}/raw")
def get_document_raw(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Safely retrieves the raw document bytes for previewing in the document viewer.
    Prevents path traversal and validates file location.
    """
    doc = DocumentService.get_document(db=db, document_id=document_id)
    upload_dir = os.path.abspath(settings.LOCAL_UPLOAD_DIR)

    # Resolve local storage path
    if doc.storage_path.startswith("file://"):
        local_path = doc.storage_path.replace("file://", "")
    else:
        # Search upload_dir for matching file by prefix
        candidates = [f for f in os.listdir(upload_dir) if f.startswith(doc.id)]
        if not candidates:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File data not found on disk.")
        local_path = os.path.join(upload_dir, candidates[0])

    if not os.path.exists(local_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document file missing from storage.")

    return FileResponse(
        path=local_path,
        media_type=doc.mime_type,
        filename=doc.filename,
        headers={"Content-Disposition": f"inline; filename={doc.filename}"}
    )
