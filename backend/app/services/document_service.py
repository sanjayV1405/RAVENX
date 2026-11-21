import os
import uuid
import re
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from app.models.document import Document
from app.models.extraction_job import ExtractionJob
from app.models.extracted_page import ExtractedPage
from app.utils.file_validators import validate_file_metadata, calculate_sha256
from app.database.supabase import supabase_service
from app.core.config import settings
from app.core.exceptions import DocumentNotFoundError, RavenXException
from app.core.logging import logger
from app.document_processing.stages.extraction import ExtractionStage


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal and shell injection."""
    base = os.path.basename(filename)
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", base)
    return clean[:200] or "document"


class DocumentService:
    @staticmethod
    def get_document(db: Session, document_id: str) -> Document:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise DocumentNotFoundError(document_id=document_id)
        return doc

    @staticmethod
    def list_documents(db: Session, skip: int = 0, limit: int = 50) -> List[Document]:
        return db.query(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    async def upload_document(
        db: Session,
        filename: str,
        file_bytes: bytes,
    ) -> Tuple[Document, bool]:
        """
        Uploads and ingests a document.
        Returns (Document, is_duplicate).
        Never modifies or overwrites the source file.
        """
        file_size = len(file_bytes)
        ext, mime_type = validate_file_metadata(filename, file_size)
        checksum = calculate_sha256(file_bytes)
        clean_name = sanitize_filename(filename)

        # 1. Duplicate detection using cryptographic SHA-256
        existing_doc = db.query(Document).filter(Document.checksum == checksum).first()
        if existing_doc:
            logger.info(f"Duplicate document detected (SHA-256: {checksum[:12]}...). Returning existing record {existing_doc.id}")
            return existing_doc, True

        doc_id = str(uuid.uuid4())
        storage_filename = f"{doc_id}_{clean_name}"

        # 2. Local storage persistence (preserves pristine uploaded bytes)
        upload_dir = os.path.abspath(settings.LOCAL_UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        local_filepath = os.path.join(upload_dir, storage_filename)
        with open(local_filepath, "wb") as f:
            f.write(file_bytes)

        # 3. Supabase upload (with transparent local fallback)
        cloud_storage_path = await supabase_service.upload_document(
            file_bytes=file_bytes,
            file_path=storage_filename,
            content_type=mime_type
        )

        storage_path = cloud_storage_path if supabase_service.is_configured else f"file://{local_filepath}"

        doc = Document(
            id=doc_id,
            filename=clean_name,
            file_extension=ext,
            file_size_bytes=file_size,
            mime_type=mime_type,
            storage_path=storage_path,
            checksum=checksum,
            status="processing",
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        logger.info(f"Registered document record ID={doc.id} ({clean_name}, {file_size} bytes)")

        # 4. Trigger Real Document Extraction
        doc_metadata = {
            "filename": clean_name,
            "extension": ext,
            "mime_type": mime_type,
            "size_bytes": file_size,
            "checksum": checksum,
        }

        try:
            extraction_result = await ExtractionStage.process(
                document_data=doc_metadata,
                file_bytes=file_bytes,
                db=db,
                document_id=doc.id
            )
            doc.page_count = extraction_result.get("page_count", 1)
            doc.status = "completed" if extraction_result.get("status") == "extracted" else "failed"
            db.commit()
            db.refresh(doc)
        except Exception as e:
            logger.error(f"Extraction execution failed for {doc.id}: {e}")
            doc.status = "failed"
            db.commit()

        return doc, False

    @staticmethod
    def get_extraction_job(db: Session, document_id: str) -> Optional[ExtractionJob]:
        return db.query(ExtractionJob).filter(ExtractionJob.document_id == document_id).order_by(ExtractionJob.created_at.desc()).first()

    @staticmethod
    def get_extracted_pages(db: Session, document_id: str, skip: int = 0, limit: int = 100) -> List[ExtractedPage]:
        job = DocumentService.get_extraction_job(db, document_id)
        if not job:
            return []
        return db.query(ExtractedPage).filter(ExtractedPage.extraction_job_id == job.id).order_by(ExtractedPage.page_number.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_extracted_page(db: Session, document_id: str, page_number: int) -> Optional[ExtractedPage]:
        job = DocumentService.get_extraction_job(db, document_id)
        if not job:
            return None
        return db.query(ExtractedPage).filter(
            ExtractedPage.extraction_job_id == job.id,
            ExtractedPage.page_number == page_number
        ).first()
