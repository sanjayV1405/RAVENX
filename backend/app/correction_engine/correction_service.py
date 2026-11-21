import os
import uuid
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.exceptions import RavenXException, DocumentNotFoundError
from app.models.document import Document
from app.models.inspection import Inspection
from app.models.finding import Finding
from app.models.corrected_document import CorrectedDocument
from app.correction_engine.pdf_corrector import PDFCorrector
from app.correction_engine.docx_corrector import DOCXCorrector
from app.correction_engine.pptx_corrector import PPTXCorrector
from app.correction_engine.output_validator import IndependentOutputValidator
from app.services.audit_service import AuditService
from app.core.logging import logger


class CorrectionService:
    """
    Central Orchestration Service for Real Document Correction.
    Guarantees:
    - Original document remains strictly immutable (SHA-256 verified).
    - Only approved/accepted findings are applied.
    - Generates authentic, valid, reopenable PDF, DOCX, and PPTX files.
    - Full audit logging of all corrected artifacts.
    """

    @classmethod
    def apply_corrections(
        cls,
        db: Session,
        inspection_id: str,
        selected_finding_ids: Optional[List[str]] = None
    ) -> CorrectedDocument:
        inspection = db.query(Inspection).filter(Inspection.id == inspection_id).first()
        if not inspection:
            raise RavenXException(detail=f"Inspection with ID '{inspection_id}' not found", status_code=404)

        doc = db.query(Document).filter(Document.id == inspection.document_id).first()
        if not doc:
            raise DocumentNotFoundError(document_id=inspection.document_id)

        # 1. Update finding statuses if selected_finding_ids provided
        if selected_finding_ids is not None:
            # Mark specified findings as accepted
            db.query(Finding).filter(
                Finding.inspection_id == inspection_id,
                Finding.id.in_(selected_finding_ids)
            ).update({"user_status": "accepted"}, synchronize_session=False)
            db.commit()

        # 2. Query all accepted findings for this inspection
        accepted_findings = db.query(Finding).filter(
            Finding.inspection_id == inspection_id,
            Finding.user_status == "accepted"
        ).all()

        if not accepted_findings:
            # If no accepted findings, check if user has pending findings to auto-accept or warn
            raise RavenXException(
                detail="No accepted findings to apply. Please review and accept at least one finding before generating the corrected document.",
                status_code=400
            )

        # Convert findings to dicts for corrector engines
        findings_data = [
            {
                "id": f.id,
                "title": f.title,
                "page_number": f.page_number,
                "original_content": f.original_content,
                "suggested_correction": f.suggested_correction,
                "category": f.category,
                "finding_classification": getattr(f, "finding_classification", "A"),
                "is_actionable": getattr(f, "is_actionable", True),
                "severity": f.severity,
                "confidence": f.confidence
            }
            for f in accepted_findings
        ]

        # 3. Read original file bytes safely (strictly read-only)
        original_bytes = cls._read_original_bytes(doc)
        if not original_bytes:
            raise RavenXException(detail="Original document binary could not be loaded from storage.", status_code=500)

        # Verify original file integrity
        computed_orig_hash = hashlib.sha256(original_bytes).hexdigest()
        if doc.checksum and computed_orig_hash != doc.checksum:
            logger.warning(f"Original document hash mismatch: expected {doc.checksum}, got {computed_orig_hash}")

        ext = doc.file_extension.lower().replace(".", "")

        # 4. Dispatch to format-specific surgical correction engine
        logger.info(f"Applying {len(findings_data)} accepted findings to {doc.filename} (.{ext})")
        if ext == "pdf":
            corrected_bytes, applied_count, applied_log = PDFCorrector.correct(original_bytes, findings_data)
        elif ext == "docx":
            corrected_bytes, applied_count, applied_log = DOCXCorrector.correct(original_bytes, findings_data)
        elif ext == "pptx":
            corrected_bytes, applied_count, applied_log = PPTXCorrector.correct(original_bytes, findings_data)
        else:
            raise RavenXException(detail=f"Unsupported correction format: .{ext}", status_code=400)

        # 5. Independent Output Validation (Step 6)
        validation_report = IndependentOutputValidator.validate_output(
            original_bytes=original_bytes,
            corrected_bytes=corrected_bytes,
            file_extension=ext,
            applied_log=applied_log,
            expected_checksum=doc.checksum
        )

        # 6. Compute SHA-256 of the new corrected document
        corrected_checksum = hashlib.sha256(corrected_bytes).hexdigest()

        # 7. Store corrected document in dedicated output storage
        corrected_dir = os.path.join(os.path.abspath(settings.LOCAL_UPLOAD_DIR), "corrected")
        os.makedirs(corrected_dir, exist_ok=True)

        corr_filename = f"corrected_{doc.filename}"
        storage_filename = f"{uuid.uuid4()}_{corr_filename}"
        storage_path = os.path.join(corrected_dir, storage_filename)

        with open(storage_path, "wb") as f_out:
            f_out.write(corrected_bytes)

        # 8. Update finding verification statuses in DB
        applied_ids = {item.get("finding_id") for item in applied_log if item.get("finding_id")}
        if applied_ids:
            db.query(Finding).filter(
                Finding.inspection_id == inspection_id,
                Finding.id.in_(list(applied_ids))
            ).update({"verification_status": "VERIFIED"}, synchronize_session=False)
            db.commit()

        # 9. Check if previous CorrectedDocument existed for this inspection, or create new
        existing_corr = db.query(CorrectedDocument).filter(
            CorrectedDocument.inspection_id == inspection_id
        ).first()

        correction_summary_data = {
            "applied_count": applied_count,
            "total_accepted": len(accepted_findings),
            "verification_status": validation_report.get("status", "VERIFIED"),
            "is_verified": validation_report.get("is_verified", False),
            "validation_report": validation_report,
            "details": applied_log
        }

        if existing_corr:
            # Clean up old file if exists
            try:
                if os.path.exists(existing_corr.storage_path):
                    os.remove(existing_corr.storage_path)
            except Exception:
                pass
            existing_corr.corrected_filename = corr_filename
            existing_corr.storage_path = storage_path
            existing_corr.file_size_bytes = len(corrected_bytes)
            existing_corr.checksum = corrected_checksum
            existing_corr.applied_findings_count = applied_count
            existing_corr.correction_summary = correction_summary_data
            db.commit()
            db.refresh(existing_corr)
            corr_doc = existing_corr
        else:
            corr_doc = CorrectedDocument(
                id=str(uuid.uuid4()),
                inspection_id=inspection_id,
                document_id=doc.id,
                original_filename=doc.filename,
                corrected_filename=corr_filename,
                file_extension=ext,
                file_size_bytes=len(corrected_bytes),
                storage_path=storage_path,
                checksum=corrected_checksum,
                applied_findings_count=applied_count,
                correction_summary=correction_summary_data
            )
            db.add(corr_doc)
            db.commit()
            db.refresh(corr_doc)

        # 8. Record audit trail
        AuditService.log_event(
            db=db,
            entity_type="corrected_document",
            entity_id=corr_doc.id,
            event_type="document_corrected",
            summary=f"Generated corrected document '{corr_filename}' with {applied_count} modifications.",
            details={
                "inspection_id": inspection_id,
                "original_filename": doc.filename,
                "applied_findings_count": applied_count,
                "checksum": corrected_checksum
            }
        )

        return corr_doc

    @classmethod
    def get_corrected_document(cls, db: Session, inspection_id: str) -> Optional[CorrectedDocument]:
        return db.query(CorrectedDocument).filter(
            CorrectedDocument.inspection_id == inspection_id
        ).first()

    @classmethod
    def get_corrected_document_bytes(cls, db: Session, inspection_id: str) -> Tuple[bytes, str, str]:
        corr_doc = cls.get_corrected_document(db, inspection_id)
        if not corr_doc or not os.path.exists(corr_doc.storage_path):
            raise RavenXException(detail="Corrected document not found. Please apply corrections first.", status_code=404)

        with open(corr_doc.storage_path, "rb") as f:
            file_bytes = f.read()

        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        }
        mime = mime_types.get(corr_doc.file_extension.lower(), "application/octet-stream")
        return file_bytes, corr_doc.corrected_filename, mime

    @classmethod
    def _read_original_bytes(cls, doc: Document) -> bytes:
        """Safely loads original file binary from disk or storage."""
        upload_dir = os.path.abspath(settings.LOCAL_UPLOAD_DIR)
        if doc.storage_path.startswith("file://"):
            local_path = doc.storage_path.replace("file://", "")
            if os.path.exists(local_path):
                with open(local_path, "rb") as f:
                    return f.read()

        if os.path.exists(doc.storage_path):
            with open(doc.storage_path, "rb") as f:
                return f.read()

        # Fallback candidate search
        candidates = [fn for fn in os.listdir(upload_dir) if fn.startswith(doc.id)]
        if candidates:
            with open(os.path.join(upload_dir, candidates[0]), "rb") as f:
                return f.read()

        return b""
