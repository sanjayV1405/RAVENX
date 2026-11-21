import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.document import Document
from app.models.extracted_page import ExtractedPage
from app.models.extraction_job import ExtractionJob
from app.models.requirement import RequirementSet, RequirementItem, RequirementAssessment, RequirementResult
from app.schemas.requirement import (
    RequirementSetCreate,
    RequirementSetResponse,
    RequirementAssessmentCreate,
    RequirementAssessmentResponse
)
from app.requirements_engine.alignment_engine import RequirementsAlignmentEngine
from app.services.audit_service import AuditService

router = APIRouter()


@router.post("/sets", response_model=RequirementSetResponse, status_code=status.HTTP_201_CREATED)
def create_requirement_set(payload: RequirementSetCreate, db: Session = Depends(get_db)):
    """Creates a new requirement set with individual checklist items."""
    req_set = RequirementSet(
        id=str(uuid.uuid4()),
        title=payload.title,
        description=payload.description,
        source_type=payload.source_type or "manual",
        reference_document_id=payload.reference_document_id
    )
    db.add(req_set)

    for item in payload.items:
        db_item = RequirementItem(
            id=str(uuid.uuid4()),
            requirement_set_id=req_set.id,
            item_text=item.item_text,
            category=item.category or "general",
            importance=item.importance or "mandatory"
        )
        db.add(db_item)

    db.commit()
    db.refresh(req_set)

    AuditService.log_event(
        db=db,
        entity_type="requirement",
        entity_id=req_set.id,
        event_type="requirement_set_created",
        summary=f"Created requirement set '{req_set.title}' with {len(payload.items)} items"
    )

    return req_set


@router.get("/sets", response_model=List[RequirementSetResponse])
def list_requirement_sets(db: Session = Depends(get_db)):
    """Lists all configured requirement sets."""
    return db.query(RequirementSet).order_by(RequirementSet.created_at.desc()).all()


@router.get("/sets/{set_id}", response_model=RequirementSetResponse)
def get_requirement_set(set_id: str, db: Session = Depends(get_db)):
    """Retrieves a single requirement set and its items."""
    req_set = db.query(RequirementSet).filter(RequirementSet.id == set_id).first()
    if not req_set:
        raise HTTPException(status_code=404, detail=f"Requirement set '{set_id}' not found.")
    return req_set


@router.post("/assess", response_model=RequirementAssessmentResponse, status_code=status.HTTP_201_CREATED)
def assess_requirements(payload: RequirementAssessmentCreate, db: Session = Depends(get_db)):
    """
    Evaluates a target document against a requirement set or manual list.
    Outputs: MET, PARTIALLY MET, MISSING, AMBIGUOUS, NOT VERIFIABLE.
    """
    doc = db.query(Document).filter(Document.id == payload.target_document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{payload.target_document_id}' not found.")

    # Fetch extracted pages for the document
    pages_records = db.query(ExtractedPage).join(ExtractionJob).filter(ExtractionJob.document_id == doc.id).all()
    pages_data = []
    full_text = ""
    for p in pages_records:
        pages_data.append({
            "page_number": p.page_number,
            "raw_text": p.raw_text or "",
            "blocks": p.blocks or [],
            "tables": p.tables or []
        })
        full_text += (p.raw_text or "") + "\n"

    # Prepare requirement items
    req_set_id = payload.requirement_set_id
    items_to_evaluate = []

    if req_set_id:
        req_set = db.query(RequirementSet).filter(RequirementSet.id == req_set_id).first()
        if not req_set:
            raise HTTPException(status_code=404, detail=f"Requirement set '{req_set_id}' not found.")
        for it in req_set.items:
            items_to_evaluate.append({
                "id": it.id,
                "item_text": it.item_text,
                "category": it.category,
                "importance": it.importance
            })
    elif payload.manual_requirements:
        # Create an ad-hoc set
        temp_set = RequirementSet(
            id=str(uuid.uuid4()),
            title=f"Ad-hoc checklist for {doc.filename}",
            description="Manually entered requirements",
            source_type="manual"
        )
        db.add(temp_set)
        for req_txt in payload.manual_requirements:
            it = RequirementItem(
                id=str(uuid.uuid4()),
                requirement_set_id=temp_set.id,
                item_text=req_txt,
                category="general",
                importance="mandatory"
            )
            db.add(it)
            items_to_evaluate.append({"id": it.id, "item_text": req_txt, "category": "general", "importance": "mandatory"})
        db.commit()
        req_set_id = temp_set.id
    else:
        raise HTTPException(status_code=400, detail="Must provide either requirement_set_id or manual_requirements.")

    # Run alignment engine
    eval_results = RequirementsAlignmentEngine.evaluate(
        target_document_name=doc.filename,
        pages_data=pages_data,
        raw_text=full_text,
        requirements=items_to_evaluate
    )

    # Calculate summary
    summary = {
        "MET": sum(1 for r in eval_results if r["status"] == "MET"),
        "PARTIALLY_MET": sum(1 for r in eval_results if r["status"] == "PARTIALLY MET"),
        "MISSING": sum(1 for r in eval_results if r["status"] == "MISSING"),
        "AMBIGUOUS": sum(1 for r in eval_results if r["status"] == "AMBIGUOUS"),
        "NOT_VERIFIABLE": sum(1 for r in eval_results if r["status"] == "NOT VERIFIABLE"),
        "total": len(eval_results)
    }

    assessment = RequirementAssessment(
        id=str(uuid.uuid4()),
        requirement_set_id=req_set_id,
        target_document_id=doc.id,
        inspection_id=payload.inspection_id,
        status="completed",
        summary=summary
    )
    db.add(assessment)

    for r in eval_results:
        res_record = RequirementResult(
            id=str(uuid.uuid4()),
            assessment_id=assessment.id,
            requirement_item_id=r.get("requirement_item_id"),
            requirement_text=r.get("requirement_text", ""),
            status=r.get("status", "NOT VERIFIABLE"),
            supporting_evidence=r.get("supporting_evidence"),
            source_document_name=r.get("source_document_name"),
            page_number=r.get("page_number"),
            bbox=r.get("bbox"),
            explanation=r.get("explanation", ""),
            confidence=r.get("confidence", 0.9)
        )
        db.add(res_record)

    db.commit()
    db.refresh(assessment)

    AuditService.log_event(
        db=db,
        entity_type="requirement",
        entity_id=assessment.id,
        event_type="requirements_assessed",
        summary=f"Assessed {len(eval_results)} requirements for '{doc.filename}': {summary['MET']} Met, {summary['MISSING']} Missing",
        details=summary
    )

    return assessment


@router.get("/assessments/{assessment_id}", response_model=RequirementAssessmentResponse)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """Retrieves full requirement assessment results."""
    assessment = db.query(RequirementAssessment).filter(RequirementAssessment.id == assessment_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")
    return assessment

