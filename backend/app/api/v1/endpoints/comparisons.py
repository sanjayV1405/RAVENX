import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.document import Document
from app.models.extracted_page import ExtractedPage
from app.models.extraction_job import ExtractionJob
from app.models.comparison import DocumentComparison, ComparisonDifference
from app.schemas.comparison import DocumentComparisonCreate, DocumentComparisonResponse
from app.comparison_engine.document_diff import DocumentComparisonEngine
from app.services.audit_service import AuditService

router = APIRouter()


def _get_document_extraction_data(db: Session, doc_id: str):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")

    pages_records = db.query(ExtractedPage).join(ExtractionJob).filter(ExtractionJob.document_id == doc.id).order_by(ExtractedPage.page_number.asc()).all()
    pages_data = []
    full_text = ""
    for p in pages_records:
        pages_data.append({
            "page_number": p.page_number,
            "raw_text": p.raw_text or "",
            "blocks": p.blocks or [],
            "tables": p.tables or [],
            "headings": p.headings or []
        })
        full_text += (p.raw_text or "") + "\n"

    return doc, {"pages": pages_data, "raw_text": full_text}


@router.post("", response_model=DocumentComparisonResponse, status_code=status.HTTP_201_CREATED)
def compare_documents(payload: DocumentComparisonCreate, db: Session = Depends(get_db)):
    """
    Executes deep multi-document comparison between base and target documents.
    Detects content, structural, and formatting differences.
    """
    base_doc, base_data = _get_document_extraction_data(db, payload.base_document_id)
    target_doc, target_data = _get_document_extraction_data(db, payload.target_document_id)

    raw_diffs = DocumentComparisonEngine.compare(base_data=base_data, target_data=target_data)

    summary = {
        "added": sum(1 for d in raw_diffs if d["diff_type"] == "added"),
        "removed": sum(1 for d in raw_diffs if d["diff_type"] == "removed"),
        "modified": sum(1 for d in raw_diffs if d["diff_type"] == "modified"),
        "potentially_inconsistent": sum(1 for d in raw_diffs if d["diff_type"] == "potentially_inconsistent"),
        "formatting_only": sum(1 for d in raw_diffs if d["diff_type"] == "formatting_only"),
        "total": len(raw_diffs)
    }

    comparison = DocumentComparison(
        id=str(uuid.uuid4()),
        base_document_id=base_doc.id,
        target_document_id=target_doc.id,
        status="completed",
        summary=summary
    )
    db.add(comparison)

    for d in raw_diffs:
        diff_record = ComparisonDifference(
            id=str(uuid.uuid4()),
            comparison_id=comparison.id,
            category=d.get("category", "content"),
            diff_type=d.get("diff_type", "modified"),
            title=d.get("title", "Difference detected"),
            base_page=d.get("base_page"),
            target_page=d.get("target_page"),
            base_content=d.get("base_content"),
            target_content=d.get("target_content"),
            explanation=d.get("explanation", ""),
            significance=d.get("significance", "medium")
        )
        db.add(diff_record)

    db.commit()
    db.refresh(comparison)

    AuditService.log_event(
        db=db,
        entity_type="comparison",
        entity_id=comparison.id,
        event_type="comparison_performed",
        summary=f"Compared '{base_doc.filename}' vs '{target_doc.filename}': {len(raw_diffs)} differences found",
        details=summary
    )

    return comparison


@router.get("/{comparison_id}", response_model=DocumentComparisonResponse)
def get_comparison(comparison_id: str, db: Session = Depends(get_db)):
    """Retrieves full comparison results."""
    comparison = db.query(DocumentComparison).filter(DocumentComparison.id == comparison_id).first()
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Comparison '{comparison_id}' not found.")
    return comparison


@router.get("", response_model=List[DocumentComparisonResponse])
def list_comparisons(db: Session = Depends(get_db)):
    """Lists recent document comparisons."""
    return db.query(DocumentComparison).order_by(DocumentComparison.created_at.desc()).limit(20).all()

