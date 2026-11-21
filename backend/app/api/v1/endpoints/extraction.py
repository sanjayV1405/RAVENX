from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.extraction import ExtractionJobResponse, ExtractedPageSummary, ExtractedPageDetail
from app.services.document_service import DocumentService

router = APIRouter()


@router.get("/documents/{document_id}/extraction", response_model=ExtractionJobResponse)
def get_extraction_status(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves the status, metadata, and error details of the extraction job for a document.
    """
    # Verify document exists
    DocumentService.get_document(db=db, document_id=document_id)
    job = DocumentService.get_extraction_job(db=db, document_id=document_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No extraction job found for document ID {document_id}"
        )
    return job


@router.get("/documents/{document_id}/pages", response_model=List[ExtractedPageSummary])
def get_extracted_pages(
    document_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieves summary records for all extracted pages/slides of a document.
    """
    DocumentService.get_document(db=db, document_id=document_id)
    pages = DocumentService.get_extracted_pages(db=db, document_id=document_id, skip=skip, limit=limit)

    summaries = []
    for p in pages:
        preview = (p.raw_text or "").strip()[:180]
        if len((p.raw_text or "").strip()) > 180:
            preview += "..."

        summaries.append(
            ExtractedPageSummary(
                id=p.id,
                extraction_job_id=p.extraction_job_id,
                page_number=p.page_number,
                word_count=p.word_count,
                has_tables=p.has_tables,
                extraction_method=p.extraction_method,
                needs_ocr=p.needs_ocr,
                ocr_confidence=p.ocr_confidence,
                preview_snippet=preview,
                created_at=p.created_at,
            )
        )
    return summaries


@router.get("/documents/{document_id}/pages/{page_number}", response_model=ExtractedPageDetail)
def get_extracted_page_detail(
    document_id: str,
    page_number: int,
    db: Session = Depends(get_db)
):
    """
    Retrieves granular structured extraction data, bboxes, typography, and content for a single page.
    """
    DocumentService.get_document(db=db, document_id=document_id)
    page = DocumentService.get_extracted_page(db=db, document_id=document_id, page_number=page_number)
    if not page:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Page {page_number} not found for document ID {document_id}"
        )
    return page

