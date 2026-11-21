import os
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.inspection import Inspection
from app.models.finding import Finding
from app.models.document import Document
from app.core.exceptions import DocumentNotFoundError, RavenXException
from app.document_processing.pipeline import DocumentInspectionPipeline
from app.core.logging import logger


class InspectionService:
    @staticmethod
    def get_inspection(db: Session, inspection_id: str) -> Optional[Inspection]:
        return db.query(Inspection).filter(Inspection.id == inspection_id).first()

    @staticmethod
    def list_inspections(db: Session, document_id: Optional[str] = None) -> List[Inspection]:
        query = db.query(Inspection)
        if document_id:
            query = query.filter(Inspection.document_id == document_id)
        return query.order_by(Inspection.created_at.desc()).all()

    @staticmethod
    async def create_inspection(
        db: Session,
        document_id: str,
        ai_provider: str = "deepseek",
        user_guidelines: Optional[str] = None
    ) -> Inspection:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise DocumentNotFoundError(document_id=document_id)

        inspection = Inspection(
            id=str(uuid.uuid4()),
            document_id=document_id,
            status="pending",
            current_stage="initializing",
            progress_percentage=0,
            ai_provider=ai_provider,
            summary={"total_findings": 0}
        )
        db.add(inspection)
        db.commit()
        db.refresh(inspection)

        # Trigger modular pipeline execution
        try:
            inspection.status = "processing"
            inspection.current_stage = "analyzing"
            inspection.progress_percentage = 20
            db.commit()

            pipeline = DocumentInspectionPipeline(ai_provider=ai_provider)
            
            # Retrieve actual persisted document bytes
            file_bytes = b""
            upload_dir = os.path.abspath(settings.LOCAL_UPLOAD_DIR)
            if doc.storage_path.startswith("file://"):
                local_path = doc.storage_path.replace("file://", "")
                if os.path.exists(local_path):
                    with open(local_path, "rb") as f:
                        file_bytes = f.read()
            elif os.path.exists(upload_dir):
                candidates = [fn for fn in os.listdir(upload_dir) if fn.startswith(doc.id)]
                if candidates:
                    with open(os.path.join(upload_dir, candidates[0]), "rb") as f:
                        file_bytes = f.read()

            result = await pipeline.execute(
                filename=doc.filename,
                file_bytes=file_bytes or b"",
                guidelines=user_guidelines,
                db=db,
                document_id=doc.id
            )

            # Store findings if any generated
            findings_data = result.get("findings", [])
            for f in findings_data:
                db_finding = Finding(
                    id=str(uuid.uuid4()),
                    inspection_id=inspection.id,
                    category=f.get("category", "micro_typography"),
                    title=f.get("title", "Detected anomaly"),
                    finding_classification=f.get("finding_classification", "A"),
                    is_actionable=f.get("is_actionable", True),
                    page_number=f.get("page_number", 1),
                    original_content=f.get("original_content", ""),
                    suggested_correction=f.get("suggested_correction", ""),
                    explanation=f.get("explanation", ""),
                    severity=f.get("severity", "medium"),
                    confidence=f.get("confidence", 0.9),
                    evidence_source=f.get("evidence_source", "deterministic_rule"),
                    bbox=f.get("bbox"),
                    char_offset_start=f.get("char_offset_start"),
                    char_offset_end=f.get("char_offset_end"),
                    detection_method=f.get("detection_method", "rule_based"),
                    user_status="needs_review"
                )
                db.add(db_finding)

            inspection.status = "completed"
            inspection.current_stage = "completed"
            inspection.progress_percentage = 100
            inspection.summary = result.get("report", {}).get("summary", {"total_findings": len(findings_data)})
            db.commit()
            db.refresh(inspection)
            logger.info(f"Inspection {inspection.id} completed with status {inspection.status}")

        except Exception as e:
            inspection.status = "failed"
            inspection.error_message = str(e)
            db.commit()
            logger.error(f"Inspection failed: {e}")

        return inspection

    @staticmethod
    def update_finding_status(
        db: Session,
        finding_id: str,
        user_status: str
    ) -> Finding:
        from datetime import datetime
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        if not finding:
            raise RavenXException(detail=f"Finding with ID {finding_id} not found", status_code=404)

        valid_statuses = ["pending", "needs_review", "accepted", "rejected", "ignored"]
        if user_status not in valid_statuses:
            raise RavenXException(
                detail=f"Invalid status '{user_status}'. Must be one of: {', '.join(valid_statuses)}",
                status_code=400
            )

        # Normalize pending to needs_review
        normalized_status = "needs_review" if user_status == "pending" else user_status
        old_status = finding.user_status
        finding.user_status = normalized_status
        finding.reviewed_at = datetime.utcnow().isoformat()
        db.commit()
        db.refresh(finding)

        # Record audit log
        from app.services.audit_service import AuditService
        event_name = "finding_restored" if normalized_status == "needs_review" else f"finding_{normalized_status}"
        AuditService.log_event(
            db=db,
            entity_type="finding",
            entity_id=finding.id,
            event_type=event_name,
            summary=f"Finding '{finding.title}' review status updated from '{old_status}' to '{normalized_status}'",
            details={
                "inspection_id": finding.inspection_id,
                "category": finding.category,
                "severity": finding.severity,
                "old_status": old_status,
                "new_status": normalized_status
            }
        )
        return finding

