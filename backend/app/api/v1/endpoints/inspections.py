from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.inspection import InspectionCreate, InspectionResponse
from app.schemas.finding import FindingStatusUpdate, FindingResponse
from app.services.inspection_service import InspectionService

router = APIRouter()


@router.post("", response_model=InspectionResponse, status_code=status.HTTP_201_CREATED)
async def create_inspection(
    payload: InspectionCreate,
    db: Session = Depends(get_db)
):
    """
    Initiates a new document inspection run across the modular pipeline.
    """
    inspection = await InspectionService.create_inspection(
        db=db,
        document_id=payload.document_id,
        ai_provider=payload.ai_provider or "deepseek",
        user_guidelines=payload.user_guidelines
    )
    return inspection


@router.get("", response_model=List[InspectionResponse])
def list_inspections(
    document_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Lists inspection runs with optional filtering by document_id."""
    return InspectionService.list_inspections(db=db, document_id=document_id)


@router.get("/{inspection_id}", response_model=InspectionResponse)
def get_inspection(
    inspection_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full inspection details including all evidence-backed findings."""
    inspection = InspectionService.get_inspection(db=db, inspection_id=inspection_id)
    if not inspection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inspection with ID {inspection_id} not found."
        )
    return inspection


@router.get("/{inspection_id}/findings", response_model=List[FindingResponse])
def get_inspection_findings(
    inspection_id: str,
    category: Optional[str] = None,
    severity: Optional[str] = None,
    user_status: Optional[str] = None,
    page_number: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieves evidence-backed findings with multi-criteria filtering:
    category, severity, user review status, and page number.
    """
    from app.models.finding import Finding
    query = db.query(Finding).filter(Finding.inspection_id == inspection_id)
    if category:
        query = query.filter(Finding.category == category)
    if severity:
        query = query.filter(Finding.severity == severity.lower())
    if user_status:
        query = query.filter(Finding.user_status == user_status.lower())
    if page_number is not None:
        query = query.filter(Finding.page_number == page_number)
    return query.order_by(Finding.page_number.asc(), Finding.created_at.asc()).all()


@router.patch("/findings/{finding_id}/status", response_model=FindingResponse)
def update_finding_review(
    finding_id: str,
    payload: FindingStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Allows user review (accept/reject/ignore) for an identified finding.
    RAVENX AI never modifies the source document automatically.
    """
    return InspectionService.update_finding_status(
        db=db,
        finding_id=finding_id,
        user_status=payload.user_status
    )


@router.get("/{inspection_id}/report.pdf")
def download_audit_report_pdf(
    inspection_id: str,
    include_excerpts: bool = True,
    include_alignment: bool = True,
    db: Session = Depends(get_db)
):
    """
    Generates and downloads an enterprise PDF audit report for the inspection run.
    """
    from fastapi.responses import Response
    from app.models.document import Document
    from app.models.finding import Finding
    from app.models.requirement import RequirementAssessment, RequirementResult
    from app.reporting.audit_report_pdf import AuditReportPDFGenerator
    from app.services.audit_service import AuditService

    inspection = InspectionService.get_inspection(db=db, inspection_id=inspection_id)
    if not inspection:
        raise HTTPException(status_code=404, detail=f"Inspection with ID {inspection_id} not found.")

    doc = db.query(Document).filter(Document.id == inspection.document_id).first()
    findings_records = db.query(Finding).filter(Finding.inspection_id == inspection_id).order_by(Finding.page_number.asc()).all()

    findings_data = []
    for f in findings_records:
        findings_data.append({
            "title": f.title,
            "category": f.category,
            "severity": f.severity,
            "confidence": f.confidence,
            "page_number": f.page_number,
            "original_content": f.original_content,
            "suggested_correction": f.suggested_correction,
            "explanation": f.explanation,
            "detection_method": f.detection_method,
            "user_status": f.user_status
        })

    # Optional requirements assessment
    req_assessment_data = None
    if include_alignment:
        assessment = db.query(RequirementAssessment).filter(RequirementAssessment.target_document_id == inspection.document_id).first()
        if assessment:
            results_list = []
            for r in assessment.results:
                results_list.append({
                    "requirement_text": r.requirement_text,
                    "status": r.status,
                    "page_number": r.page_number,
                    "supporting_evidence": r.supporting_evidence,
                    "explanation": r.explanation
                })
            req_assessment_data = {"summary": assessment.summary, "results": results_list}

    document_info = {
        "filename": doc.filename if doc else "document",
        "file_extension": doc.file_extension if doc else "",
        "page_count": doc.page_count,
        "checksum": doc.checksum if doc else "N/A"
    }

    inspection_info = {
        "id": inspection.id,
        "ai_provider": inspection.ai_provider,
        "status": inspection.status,
        "created_at": str(inspection.created_at)
    }

    pdf_bytes = AuditReportPDFGenerator.generate(
        document_info=document_info,
        inspection_info=inspection_info,
        findings=findings_data,
        requirements_assessment=req_assessment_data,
        include_excerpts=include_excerpts
    )

    AuditService.log_event(
        db=db,
        entity_type="report",
        entity_id=inspection_id,
        event_type="report_generated",
        summary=f"PDF Audit report generated for inspection {inspection_id[:8]} ({len(findings_data)} findings)"
    )

    filename = f"ravenx_audit_{doc.filename.rsplit('.', 1)[0] if doc else 'doc'}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

